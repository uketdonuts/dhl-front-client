#!/usr/bin/env python3
"""
Script para extraer los 3 pesos de un tracking number usando DHL REST API
Equivalente a Weight, DimWeight, ActualWeight del SOAP
"""
import os
import sys
import json
from decimal import Decimal, ROUND_HALF_UP

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from dhl_api.services import DHLService

def round_2_decimals(value):
    """Redondeo ROUND_HALF_UP a 2 decimales como en el backend"""
    try:
        if value is None:
            return None
        return float(Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
    except Exception:
        return 0.0

def extract_three_weights_per_piece(tracking_number):
    """
    Extrae los 3 pesos por pieza del tracking DHL:
    - Weight (declarado/declared_weight)  
    - DimWeight (dimensional/dhl_dimensional_weight)
    - ActualWeight (repesaje/actual_weight_reweigh)
    """
    # Usar credenciales del proyecto
    username = os.getenv('DHL_USERNAME', 'apO3fS5mJ8zT7h')
    password = os.getenv('DHL_PASSWORD', 'J^4oF@1qW!0qS!5b')
    base_url = os.getenv('DHL_BASE_URL', 'https://express.api.dhl.com')
    environment = os.getenv('DHL_ENVIRONMENT', 'production')
    
    print(f"🔍 Consultando DHL REST para tracking: {tracking_number}")
    print(f"📡 Endpoint: {base_url}")
    print(f"🌐 Environment: {environment}")
    print("-" * 60)
    
    # Crear servicio DHL
    dhl_service = DHLService(
        username=username,
        password=password,
        base_url=base_url,
        environment=environment
    )
    
    # Obtener tracking info
    result = dhl_service.get_tracking(tracking_number)
    
    if not result.get('success'):
        print(f"❌ Error: {result.get('message', 'Unknown error')}")
        return None
    
    print(f"✅ Tracking exitoso")
    print(f"📦 Status: {result.get('status', 'N/A')}")
    
    # Extraer piece details
    pieces = result.get('piece_details', [])
    shipment_info = result.get('shipment_info', {})
    
    print(f"📊 Total piezas: {len(pieces)}")
    print(f"⚖️  Peso total envío: {shipment_info.get('total_weight', 0)} {shipment_info.get('weight_unit', 'KG')}")
    print("-" * 60)
    
    # Procesar cada pieza
    three_weights_summary = {
        'tracking_number': tracking_number,
        'total_pieces': len(pieces),
        'shipment_total_weight': shipment_info.get('total_weight', 0),
        'weight_unit': shipment_info.get('weight_unit', 'KG'),
        'pieces': []
    }
    
    sum_declared = Decimal('0')
    sum_actual = Decimal('0') 
    sum_dimensional = Decimal('0')
    
    for idx, piece in enumerate(pieces, 1):
        piece_id = piece.get('piece_id', f'Piece-{idx}')
        weight_info = piece.get('weight_info', {})
        
        # Extraer los 3 pesos con múltiples fallbacks
        # 1. Weight (declarado)
        declared = (
            weight_info.get('declared_weight') or
            piece.get('declared_weight') or
            piece.get('peso_declarado') or
            piece.get('weight') or
            0
        )
        
        # 2. ActualWeight (repesaje)
        actual = (
            weight_info.get('actual_weight_reweigh') or
            weight_info.get('actual_weight') or
            piece.get('actual_weight') or
            piece.get('repesaje') or
            0
        )
        
        # 3. DimWeight (dimensional)
        dimensional = (
            weight_info.get('dhl_dimensional_weight') or
            piece.get('dhl_dimensional_weight') or
            0
        )
        
        # Redondear cada peso a 2 decimales
        declared_rounded = round_2_decimals(declared)
        actual_rounded = round_2_decimals(actual)
        dimensional_rounded = round_2_decimals(dimensional)
        
        # Acumular para sumas (round-then-sum como en SOAP)
        if declared_rounded:
            sum_declared += Decimal(str(declared_rounded))
        if actual_rounded:
            sum_actual += Decimal(str(actual_rounded))
        if dimensional_rounded:
            sum_dimensional += Decimal(str(dimensional_rounded))
        
        piece_weights = {
            'piece_number': idx,
            'piece_id': piece_id,
            'declared_weight': declared_rounded,    # Weight en SOAP
            'actual_weight': actual_rounded,        # ActualWeight en SOAP
            'dimensional_weight': dimensional_rounded, # DimWeight en SOAP
            'unit': shipment_info.get('weight_unit', 'KG')
        }
        
        three_weights_summary['pieces'].append(piece_weights)
        
        # Imprimir formato SOAP-style
        print(f"📦 Pieza {idx} ({piece_id}):")
        print(f"   <Weight>{declared_rounded:.3f}</Weight>")
        print(f"   <DimWeight>{dimensional_rounded:.3f}</DimWeight>") 
        print(f"   <ActualWeight>{actual_rounded:.3f}</ActualWeight>")
        print()
    
    # Calcular sumas totales (estilo SOAP)
    sum_declared_final = round_2_decimals(sum_declared)
    sum_actual_final = round_2_decimals(sum_actual)
    sum_dimensional_final = round_2_decimals(sum_dimensional)
    
    # Determinar el peso mayor para cotización
    highest_weight = max(
        shipment_info.get('total_weight', 0),
        sum_declared_final or 0,
        sum_actual_final or 0,
        sum_dimensional_final or 0
    )
    
    three_weights_summary.update({
        'totals': {
            'sum_declared': sum_declared_final,
            'sum_actual': sum_actual_final,
            'sum_dimensional': sum_dimensional_final,
            'highest_for_quote': highest_weight,
            'unit': shipment_info.get('weight_unit', 'KG')
        }
    })
    
    print("=" * 60)
    print("📊 RESUMEN DE PESOS (Estilo SOAP):")
    print(f"   Suma Declarados: {sum_declared_final:.3f} KG")
    print(f"   Suma Actuales:   {sum_actual_final:.3f} KG") 
    print(f"   Suma Dimensionales: {sum_dimensional_final:.3f} KG")
    print(f"   Peso Total Envío: {shipment_info.get('total_weight', 0):.3f} KG")
    print(f"   🏆 Mayor (para cotizar): {highest_weight:.3f} KG")
    print("=" * 60)
    
    return three_weights_summary

if __name__ == "__main__":
    tracking_number = "6869687790"
    if len(sys.argv) > 1:
        tracking_number = sys.argv[1]
    
    result = extract_three_weights_per_piece(tracking_number)
    
    if result:
        print("\n🔧 JSON de salida:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
