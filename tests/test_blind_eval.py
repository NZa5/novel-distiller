import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / 'evaluation'))
import blind_eval


def experiment():
    facts = '一人等候，另一人到来。'
    return {'schema_version': '1.0', 'experiment_id': 'test', 'reader_ids': ['reader1', 'reader2'],
        'items': [{'item_id': 'scene1', 'facts': facts, 'cue_audit': '已统一姓名与地点；仅为合成工程夹具',
            'original_source': 'synthetic fixture', 'profile_sha256': 'a' * 64,
            'generation_settings': 'synthetic; no model call',
            'candidates': {arm: {'text': text, 'facts_sha256': blind_eval.digest(facts)}
                for arm, text in zip(blind_eval.ARMS, ['他在门前等，她来了。', '他停在门边，她来了。', '他站在门旁，她来了。'])}}]}


class BlindEvalTests(unittest.TestCase):
    def test_reproducible_and_blinded(self):
        first = blind_eval.prepare(experiment(), seed=42)
        self.assertEqual(first, blind_eval.prepare(experiment(), seed=42))
        self.assertNotIn('original', str(first[0]))
        self.assertEqual(len(first[0]['trials']), 2)

    def test_complete_scores_and_incomplete_results(self):
        blind, key = blind_eval.prepare(experiment())
        answers = [{'trial_id': trial['trial_id'], 'reader_id': trial['reader_id'],
            'choice': next(label for label, arm in trial['mapping'].items() if arm == 'profile_guided')}
            for trial in key['trials']]
        result = blind_eval.score(blind, key, answers)
        self.assertEqual(result['status'], 'complete')
        self.assertEqual(result['profile_minus_baseline_rate'], 1)
        self.assertEqual(blind_eval.score(blind, key, answers[:1])['status'], 'incomplete')
        self.assertIsNone(blind_eval.score(blind, key, [])['profile_minus_baseline_rate'])
        with self.assertRaisesRegex(ValueError, '重复'):
            blind_eval.score(blind, key, answers + answers[:1])

    def test_invalid_fact_length_and_cue_data_rejected(self):
        for mutation in ('facts', 'length', 'cue'):
            exp = experiment()
            if mutation == 'facts':
                exp['items'][0]['candidates']['original']['facts_sha256'] = 'wrong'
            elif mutation == 'length':
                exp['items'][0]['candidates']['original']['text'] *= 10
            else:
                exp['items'][0]['cue_audit'] = ''
            with self.assertRaises(ValueError):
                blind_eval.prepare(exp)

    def test_tampered_blind_file_rejected(self):
        blind, key = blind_eval.prepare(experiment())
        blind['trials'][0]['candidates']['A'] = '替换'
        with self.assertRaisesRegex(ValueError, '不一致'):
            blind_eval.score(blind, key, [])


if __name__ == '__main__':
    unittest.main()
