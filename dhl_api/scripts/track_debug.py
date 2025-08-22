import os
import json
import sys
from datetime import datetime

# Ensure we can import the project modules regardless of CWD
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from dhl_api.services import DHLService
from decimal import Decimal, ROUND_HALF_UP


def round2(x):
    try:
        return float(f"{float(x):.2f}")
    except Exception:
        return 0.0


def main():
    if len(sys.argv) < 2:
        print("Usage: track_debug.py <tracking_number>")
        sys.exit(1)
    tracking_number = sys.argv[1]

    username = os.getenv('DHL_USERNAME', '')
    password = os.getenv('DHL_PASSWORD', '')
    base_url = os.getenv('DHL_BASE_URL', 'https://express.api.dhl.com')
    environment = os.getenv('DHL_ENVIRONMENT', 'production')

    svc = DHLService(username=username, password=password, base_url=base_url, environment=environment)

    result = svc.get_tracking(tracking_number)

    # Compute weight candidates from parsed result
    shipment_info = result.get('shipment_info', {})
    pieces = result.get('piece_details', []) or []
    raw = result.get('raw_data') or {}
    raw_shipments = raw.get('shipments') or []
    raw_shipment = raw_shipments[0] if raw_shipments else {}
    raw_pieces = raw_shipment.get('pieces') or []
    # Try to get raw totalWeight from multiple shapes
    raw_total_weight = None
    try:
        if isinstance(raw_shipment.get('totalWeight'), dict):
            raw_total_weight = raw_shipment['totalWeight'].get('value')
        elif 'totalWeight' in raw_shipment:
            raw_total_weight = raw_shipment.get('totalWeight')
        elif 'details' in raw_shipment:
            tw = raw_shipment['details'].get('totalWeight')
            if isinstance(tw, dict):
                raw_total_weight = tw.get('value')
            else:
                raw_total_weight = tw
    except Exception:
        raw_total_weight = None

    orig_total = float(shipment_info.get('total_weight') or 0)
    piece_weights = []  # chosen per-piece weight (backend picks actual > declared)
    piece_declared = []
    piece_actual = []
    piece_dimensional = []  # raw per-piece dimensional (unrounded)
    piece_dimensional_rounded = []  # per-piece rounded to 2 decimals
    pieces_summary = []
    dhl_piece_dimensional = []
    for idx, p in enumerate(pieces, start=1):
        # selected weight field (already rounded)
        w = p.get('weight') or 0
        try:
            piece_weights.append(float(w))
        except Exception:
            piece_weights.append(0.0)

        # declared and actual (reweigh) if present
        dw = p.get('peso_declarado')
        aw = p.get('repesaje')
        try:
            piece_declared.append(float(dw) if dw is not None else 0.0)
        except Exception:
            piece_declared.append(0.0)
        try:
            piece_actual.append(float(aw) if aw is not None else (float(w) if w else 0.0))
        except Exception:
            try:
                piece_actual.append(float(w))
            except Exception:
                piece_actual.append(0.0)

        # dimensional from dimensions if present (LxWxH/5000)
        dims = p.get('dimensions') or {}
        try:
            L = float(dims.get('length') or 0)
            W = float(dims.get('width') or 0)
            H = float(dims.get('height') or 0)
            dim_w = (L * W * H) / 5000 if L > 0 and W > 0 and H > 0 else 0.0
        except Exception:
            dim_w = 0.0
        piece_dimensional.append(dim_w)
        # Also store rounded per-piece dimensional
        try:
            piece_dimensional_rounded.append(float(Decimal(str(dim_w)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)))
        except Exception:
            piece_dimensional_rounded.append(round2(dim_w))

        # DHL-provided dimensional if present
        dhl_dim_w = p.get('dhl_dimensional_weight') or 0
        try:
            dhl_piece_dimensional.append(float(dhl_dim_w))
        except Exception:
            dhl_piece_dimensional.append(0.0)

        pieces_summary.append({
            'piece': idx,
            'declared': round2(dw),
            'actual': round2(aw) if aw is not None else round2(w),
            'dimensional': round2(dim_w),
            'dhl_dimensional': round2(dhl_dim_w),
            'selected_for_sum': round2(w)
        })

    sum_pieces = sum(piece_weights) if piece_weights else 0.0
    max_piece = max(piece_weights) if piece_weights else 0.0
    sum_declared = sum(piece_declared) if piece_declared else 0.0
    sum_actual = sum(piece_actual) if piece_actual else 0.0
    sum_dimensional_raw = sum(piece_dimensional) if piece_dimensional else 0.0
    # sum then round (HALF_UP)
    try:
        sum_dimensional_sum_then_round = float(Decimal(str(sum_dimensional_raw)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
    except Exception:
        sum_dimensional_sum_then_round = round2(sum_dimensional_raw)
    # round each then sum
    sum_dimensional_round_then_sum = sum(piece_dimensional_rounded) if piece_dimensional_rounded else 0.0
    try:
        sum_dimensional_round_then_sum = float(Decimal(str(sum_dimensional_round_then_sum)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
    except Exception:
        sum_dimensional_round_then_sum = round2(sum_dimensional_round_then_sum)
    max_dimensional = max(piece_dimensional) if piece_dimensional else 0.0
    dhl_sum_dimensional = sum(dhl_piece_dimensional) if dhl_piece_dimensional else 0.0

    highest = max(
        orig_total,
        sum_pieces,
        sum_actual,
        sum_declared,
        sum_dimensional_sum_then_round,
        sum_dimensional_round_then_sum,
        max_piece,
        max_dimensional,
    )

    output = {
        'success': bool(result.get('success')),
        'tracking_number': shipment_info.get('tracking_number') or result.get('tracking_number') or tracking_number,
        'status': result.get('status') or shipment_info.get('status'),
        'weights': {
            'shipment_total': round2(orig_total),
            'sum_pieces_selected': round2(sum_pieces),
            'sum_declared': round2(sum_declared),
            'sum_actual': round2(sum_actual),
            'sum_dimensional_sum_then_round': round2(sum_dimensional_sum_then_round),
            'sum_dimensional_round_then_sum': round2(sum_dimensional_round_then_sum),
            'max_piece_selected': round2(max_piece),
            'max_piece_dimensional': round2(max_dimensional),
            'dhl_sum_dimensional': round2(dhl_sum_dimensional),
            'dhl_total_dimensional': round2(shipment_info.get('dhl_total_dimensional_weight')) if shipment_info.get('dhl_total_dimensional_weight') is not None else None,
            'highest_for_quote': round2(highest),
            'raw_total_weight': round2(raw_total_weight) if raw_total_weight is not None else None,
        },
        'counts': {
            'pieces': result.get('total_pieces', len(pieces)),
            'events': result.get('total_events', 0)
        },
        'origin': shipment_info.get('origin'),
        'destination': shipment_info.get('destination'),
        'service': shipment_info.get('service_type') or shipment_info.get('service'),
        'timestamp': datetime.now().isoformat(),
        # Keep a small preview of raw for debugging only
        'http_status': result.get('http_status'),
    'pieces': pieces_summary,
        'raw_pieces': [
            {
                'declared_raw': rp.get('weight'),
                'actual_raw': rp.get('actualWeight'),
                'dimensions_raw': rp.get('dimensions')
            } for rp in raw_pieces
        ],
    }

    print(json.dumps(output, ensure_ascii=False))


if __name__ == '__main__':
    main()
