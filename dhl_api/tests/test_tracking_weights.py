from django.urls import reverse
from rest_framework.test import APITestCase
from unittest.mock import patch


class TrackingWeightsSummaryTests(APITestCase):
    @patch('dhl_api.views.DHLService.get_tracking')
    def test_weights_summary_includes_three_weights_and_highest(self, mock_get_tracking):
        # Mock DHL tracking response with piece weights that exercise rounding
        mock_get_tracking.return_value = {
            'success': True,
            'tracking_number': '1234567890',
            'shipment_info': {
                'total_weight': 100.0,
                'weight_unit': 'KG',
            },
            'piece_details': [
                {'weight_info': {'selected_weight': 30.124}},  # -> 30.12
                {'weight_info': {'selected_weight': 70.005}},  # -> 70.01
            ],
            'events': [],
            'total_events': 0,
            'total_pieces': 2,
            'message': 'ok'
        }

        url = reverse('tracking')
        resp = self.client.post(url, {'tracking_number': '1234567890'}, format='json')

        self.assertEqual(resp.status_code, 200)
        self.assertIn('weights_summary', resp.data)
        ws = resp.data['weights_summary']
        w3 = resp.data.get('weights_three_sums', {
            'sum_declared': None,
            'sum_actual': None,
            'sum_dimensional': None,
            'highest_for_quote': None
        })

        # Print nine values (each on its own line): 3 summary, 3 soap, 3 highest
        highest_summary = ws.get('highest_for_quote')
        highest_soap = w3.get('highest_for_quote')
        overall_highest = max([v for v in [highest_summary, highest_soap] if v is not None])
        print("WEIGHTS DEBUG (test1):")
        print(f"summary.shipment_total={ws.get('shipment_total')}")
        print(f"summary.sum_pieces={ws.get('sum_pieces')}")
        print(f"summary.max_piece={ws.get('max_piece')}")
        print(f"soap.sum_declared={w3.get('sum_declared')}")
        print(f"soap.sum_actual={w3.get('sum_actual')}")
        print(f"soap.sum_dimensional={w3.get('sum_dimensional')}")
        print(f"highest.summary={highest_summary}")
        print(f"highest.soap={highest_soap}")
        print(f"highest.overall={overall_highest}")

        # Validate rounded values and selection logic
        self.assertEqual(ws['unit'], 'KG')
        self.assertEqual(ws['shipment_total'], 100.0)
        self.assertEqual(ws['sum_pieces'], 100.13)  # 30.12 + 70.01
        self.assertEqual(ws['max_piece'], 70.01)
        self.assertEqual(ws['highest_for_quote'], 100.13)

        # Per-piece triples (may be None when not provided by mock)
        wbp = resp.data.get('weights_by_piece', [])
        print("BY PIECE (test1):")
        for item in wbp:
            print(f"piece[{item.get('index')}].declared={item.get('declared')}")
            print(f"piece[{item.get('index')}].actual={item.get('actual')}")
            print(f"piece[{item.get('index')}].dimensional={item.get('dimensional')}")

    @patch('dhl_api.views.DHLService.get_tracking')
    def test_account_gating_when_missing_dhl_volumetric(self, mock_get_tracking):
        """If DHL dimensional weight is missing/zero, backend should block quote_with_weight and suggest creating account."""
        mock_get_tracking.return_value = {
            'success': True,
            'tracking_number': 'NO-VOL-001',
            'shipment_info': {
                'total_weight': 0.36,
                'weight_unit': 'KG',
                'dhl_total_dimensional_weight': 0.0,  # explicitly missing
            },
            'piece_details': [
                {
                    'piece_id': 'P1',
                    'peso_declarado': 0.5,
                    'repesaje': 0.36,
                    'dhl_dimensional_weight': 0.0,
                    'weight_info': {
                        'declared_weight': 0.5,
                        'actual_weight_reweigh': 0.36,
                        'dhl_dimensional_weight': 0.0
                    }
                }
            ],
            'events': [],
            'total_events': 0,
            'total_pieces': 1,
            'message': 'ok'
        }

        url = reverse('tracking')
        resp = self.client.post(url, {'tracking_number': 'NO-VOL-001'}, format='json')

        self.assertEqual(resp.status_code, 200)
        # Ensure new flags are present and set correctly
        self.assertIn('account_requirements', resp.data)
        self.assertIn('quote_with_weight', resp.data)
        ar = resp.data['account_requirements']
        qw = resp.data['quote_with_weight']

        self.assertFalse(ar.get('volumetric_from_dhl'))
        self.assertTrue(ar.get('needs_account_for_quote'))
        self.assertEqual(ar.get('reason'), 'missing_dhl_volumetric_weight')
        self.assertFalse(qw.get('allowed'))
        self.assertEqual(qw.get('blocked_reason'), 'missing_dhl_volumetric_weight')
        # Suggested weight should be populated from highest_for_quote if available
        self.assertIsNotNone(qw.get('suggested_weight'))

    @patch('dhl_api.views.DHLService.get_tracking')
    def test_three_sums_soap_style_and_highest(self, mock_get_tracking):
        # Two pieces with declared, actual (repesaje), and dimensional weights
        # Expect: sum_declared=45.00, sum_actual=60.00, sum_dimensional=62.31, highest=62.31
        mock_get_tracking.return_value = {
            'success': True,
            'tracking_number': 'ABC123',
            'shipment_info': {
                'total_weight': 44.9,
                'weight_unit': 'KG',
            },
            'piece_details': [
                {'weight_info': {
                    'declared_weight': 35.0,
                    'actual_weight': 49.5,
                    'dhl_dimensional_weight': 52.31
                }},
                {'weight_info': {
                    'declared_weight': 10.0,
                    'actual_weight': 10.5,
                    'dhl_dimensional_weight': 9.995  # -> 10.00 (ROUND_HALF_UP)
                }},
            ],
            'events': [],
            'total_events': 0,
            'total_pieces': 2,
            'message': 'ok'
        }

        url = reverse('tracking')
        resp = self.client.post(url, {'tracking_number': 'ABC123'}, format='json')

        self.assertEqual(resp.status_code, 200)
        self.assertIn('weights_three_sums', resp.data)
        w3 = resp.data['weights_three_sums']
        ws = resp.data.get('weights_summary', {})

        # Print nine values (each on its own line): 3 summary, 3 soap, 3 highest
        highest_summary = ws.get('highest_for_quote')
        highest_soap = w3.get('highest_for_quote')
        overall_highest = max([v for v in [highest_summary, highest_soap] if v is not None])
        print("WEIGHTS DEBUG (test2):")
        print(f"summary.shipment_total={ws.get('shipment_total')}")
        print(f"summary.sum_pieces={ws.get('sum_pieces')}")
        print(f"summary.max_piece={ws.get('max_piece')}")
        print(f"soap.sum_declared={w3.get('sum_declared')}")
        print(f"soap.sum_actual={w3.get('sum_actual')}")
        print(f"soap.sum_dimensional={w3.get('sum_dimensional')}")
        print(f"highest.summary={highest_summary}")
        print(f"highest.soap={highest_soap}")
        print(f"highest.overall={overall_highest}")

        self.assertEqual(w3['unit'], 'KG')
        self.assertEqual(w3['sum_declared'], 45.0)
        self.assertEqual(w3['sum_actual'], 60.0)
        self.assertEqual(w3['sum_dimensional'], 62.31)
        self.assertEqual(w3['highest_for_quote'], 62.31)

        # Per-piece triples assertion and print
        wbp = resp.data.get('weights_by_piece', [])
        self.assertEqual(len(wbp), 2)
        print("BY PIECE (test2):")
        for item in wbp:
            print(f"piece[{item.get('index')}].declared={item.get('declared')}")
            print(f"piece[{item.get('index')}].actual={item.get('actual')}")
            print(f"piece[{item.get('index')}].dimensional={item.get('dimensional')}")
        # Validate rounding and mapping
        self.assertEqual(wbp[0]['declared'], 35.0)
        self.assertEqual(wbp[0]['actual'], 49.5)
        self.assertEqual(wbp[0]['dimensional'], 52.31)
        self.assertEqual(wbp[1]['declared'], 10.0)
        self.assertEqual(wbp[1]['actual'], 10.5)
        self.assertEqual(wbp[1]['dimensional'], 10.0)
