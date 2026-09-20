#!/usr/bin/env python3
"""
Unit tests for the vitals / lab extractors in scripts/extraction_patterns.py

These guard against the regressions that filled health_metrics with dates
read as blood pressures, zip codes read as temperatures, and sentence
fragments read as lab results.
"""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.extraction_patterns import (
    extract_blood_pressure_readings,
    extract_temperature_reading,
    extract_vital_sign_readings,
    extract_lab_result_line,
    extract_health_log_table_readings,
)


class TestBloodPressure(unittest.TestCase):

    def test_labelled_reading(self):
        readings = extract_blood_pressure_readings('Blood Pressure 120/70 05/07/2025 11:46 AM EDT')
        self.assertEqual(readings, [{'systolic': 120, 'diastolic': 70, 'text': '120/70'}])

    def test_bp_abbreviation_and_unit(self):
        self.assertEqual(extract_blood_pressure_readings('BP: 118/76')[0]['text'], '118/76')
        self.assertEqual(extract_blood_pressure_readings('118/76 mmHg')[0]['text'], '118/76')

    def test_dates_and_dosages_are_not_readings(self):
        for line in ['albuterol (ProAir HFA) 90 mcg/actuation inhaler (Started 8/29/2024)',
                     'Food aversion 12/19/2024',
                     'Take 1/2 tablet daily',
                     'Blood Pressure 12/19/2024']:
            self.assertEqual(extract_blood_pressure_readings(line), [], line)

    def test_implausible_values_rejected(self):
        self.assertEqual(extract_blood_pressure_readings('BP 300/200'), [])
        self.assertEqual(extract_blood_pressure_readings('BP 70/120'), [])


class TestTemperature(unittest.TestCase):

    def test_portal_line_is_one_reading(self):
        reading = extract_temperature_reading('Temperature 36.8 °C (98.3 °F) 05/07/2025 11:46 AM EDT')
        self.assertEqual(reading, {'value': 36.8, 'unit': 'C'})

    def test_labelled_fahrenheit(self):
        self.assertEqual(extract_temperature_reading('Temp: 98.6 F'), {'value': 98.6, 'unit': 'F'})

    def test_fever_is_a_label_too(self):
        # What a person writes in their own log, and the reading most worth keeping.
        for line in ['fever 101.2F', 'Fever: 101.2 F', 'fever of 101.2F']:
            self.assertEqual(extract_temperature_reading(line), {'value': 101.2, 'unit': 'F'}, line)

    def test_numbers_followed_by_a_letter_are_not_temperatures(self):
        for line in ['BROOKLINE, MA 02445 Former / Aliases',
                     '2445 Fenway Park',
                     '12 cups of coffee',
                     'Temp 2445 F',
                     'Fever reducer given',
                     'Fever 2445 F']:
            self.assertEqual(extract_temperature_reading(line), {}, line)


class TestOtherVitals(unittest.TestCase):

    def test_pulse_weight_height_saturation(self):
        self.assertEqual(extract_vital_sign_readings('Pulse 93 05/07/2025 11:46 AM EDT'),
                         [{'metric_type': 'heart_rate', 'value': 93.0, 'unit': 'bpm'}])
        self.assertEqual(extract_vital_sign_readings('Weight 53.1 kg (117 lb)'),
                         [{'metric_type': 'weight', 'value': 53.1, 'unit': 'kg'}])
        self.assertEqual(extract_vital_sign_readings('Height 162.6 cm (5\' 4")'),
                         [{'metric_type': 'height', 'value': 162.6, 'unit': 'cm'}])
        self.assertEqual(extract_vital_sign_readings('Oxygen Saturation 100%'),
                         [{'metric_type': 'oxygen_saturation', 'value': 100.0, 'unit': '%'}])

    def test_pulse_is_not_a_date(self):
        self.assertEqual(extract_vital_sign_readings('Pulse 12/19/2024'), [])


class TestLabResults(unittest.TestCase):

    def test_result_with_range(self):
        lab = extract_lab_result_line('UROBILINOGEN UR 0.2 mg/dL 0.2-1.0 WINCHESTER')
        self.assertEqual(lab['name'], 'UROBILINOGEN UR')
        self.assertEqual(lab['value'], 0.2)
        self.assertEqual(lab['unit'], 'mg/dL')
        self.assertEqual((lab['normal_min'], lab['normal_max']), (0.2, 1.0))
        self.assertFalse(lab['is_abnormal'])

    def test_abnormal_flag(self):
        lab = extract_lab_result_line('TSH 6.10 mIU/L 0.40-4.50')
        self.assertTrue(lab['is_abnormal'])

    def test_threshold_value_keeps_text(self):
        lab = extract_lab_result_line('CRP <0.30 mg/dL')
        self.assertIsNone(lab['value'])
        self.assertEqual(lab['value_text'], '<0.30')

    def test_prose_and_addresses_are_not_results(self):
        for line in ['Helen Example 100 Summit',
                     'Jane Example is a 34 y',
                     'Suite 100 New',
                     'In the past 12 months',
                     'Glucose 94 on',
                     '400 K/uL 1:26 PM HOSPITAL LAB']:
            self.assertEqual(extract_lab_result_line(line), {}, line)


class TestHealthLogTable(unittest.TestCase):

    LOG = '''Name: Patient | DOB: 1/1/1990
Blood Pressure
All readings
Date Value (mmHg) Entry type
Nov 18, 2019, 8:56 AM 110/70 Clinic
Oct 3, 2019, 9:44 AM 12/19/2024 Clinic
Pulse
All readings
Date Value (bpm) Entry type
Nov 18, 2019, 8:56 AM 72 Clinic
Jan 1, 2019, 8:00 AM 999 Clinic
'''

    def test_rows_take_their_meaning_from_the_section(self):
        readings = extract_health_log_table_readings(self.LOG)
        self.assertEqual([(r['metric_type'], r['value'], r['unit'], r['date_text']) for r in readings],
                         [('blood_pressure', 110.0, 'mmHg', 'Nov 18, 2019'),
                          ('heart_rate', 72.0, 'bpm', 'Nov 18, 2019')])
        self.assertEqual(readings[0]['notes'], 'Diastolic: 70')
        self.assertEqual(readings[0]['time_text'], '8:56 AM')

    def test_nothing_before_a_section_heading(self):
        self.assertEqual(extract_health_log_table_readings('Nov 18, 2019, 8:56 AM 110/70 Clinic'), [])


if __name__ == '__main__':
    unittest.main()
