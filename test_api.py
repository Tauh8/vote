import requests
import json
import time
import unittest
from typing import Dict, Tuple

BASE_URL = 'http://localhost:5000'

class TestVotingSystem(unittest.TestCase):
    def setUp(self):
        """测试前的准备工作"""
        # 存储测试过程中创建的凭证
        self.test_credentials = {}
        
    def register_voter(self, voter_id: str) -> Tuple[bool, Dict]:
        """注册新投票者并返回凭证"""
        response = requests.post(
            f'{BASE_URL}/api/register',
            json={'voter_id': voter_id}
        )
        return response.status_code == 200, response.json()
        
    def prepare_vote(self, voter_id: str, vote: str, vote_randomness: str) -> Tuple[bool, Dict]:
        """准备投票（生成投票承诺）"""
        response = requests.post(
            f'{BASE_URL}/api/prepare-vote',
            json={
                'voter_id': voter_id,
                'vote': vote,
                'vote_randomness': vote_randomness
            }
        )
        return response.status_code == 200, response.json()
        
    def create_identity_proof(self, voter_id: str, private_key: int, public_key: int) -> Dict:
        """创建身份证明"""
        from voting.zk_proof import ZKProof
        zk = ZKProof()
        return zk.create_identity_proof(private_key, public_key)
        
    def test_01_registration(self):
        """测试投票者注册流程"""
        print("\n=== 测试注册功能 ===")
        
        # 测试正常注册
        success, response = self.register_voter('test_voter_1')
        self.assertTrue(success)
        self.assertTrue(response['success'])
        self.assertIn('data', response)
        self.test_credentials['voter1'] = response['data']
        print("注册新投票者成功")
        
        # 测试重复注册
        success, response = self.register_voter('test_voter_1')
        self.assertFalse(success)
        self.assertFalse(response['success'])
        print("重复注册被正确阻止")
        
    def test_02_identity_verification(self):
        """测试身份验证"""
        print("\n=== 测试身份验证 ===")
        
        if 'voter1' not in self.test_credentials:
            self.skipTest("需要先完成注册测试")
            
        credentials = self.test_credentials['voter1']
        identity_proof = self.create_identity_proof(
            credentials['voter_id'],
            int(credentials['private_key']),
            int(credentials['public_key'])
        )
        
        response = requests.post(
            f'{BASE_URL}/api/verify-identity',
            json={
                'voter_id': credentials['voter_id'],
                'identity_proof': identity_proof
            }
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertTrue(data['is_valid'])
        print("身份验证成功")
        
    def test_03_voting_flow(self):
        """测试完整投票流程"""
        print("\n=== 测试投票流程 ===")
        
        # 开始投票会话
        response = requests.post(
            f'{BASE_URL}/api/start',
            json={'duration': 30}
        )
        self.assertEqual(response.status_code, 200)
        print("开始投票会话")
        
        # 注册新投票者
        success, response = self.register_voter('test_voter_2')
        self.assertTrue(success)
        credentials = response['data']
        self.test_credentials['voter2'] = credentials
        print("注册新投票者成功")
        
        # 准备投票
        success, vote_prep = self.prepare_vote(
            credentials['voter_id'],
            'A',
            credentials['vote_randomness']
        )
        self.assertTrue(success)
        vote_proof = vote_prep['data']
        print("准备投票成功")
        
        # 创建身份证明
        identity_proof = self.create_identity_proof(
            credentials['voter_id'],
            int(credentials['private_key']),
            int(credentials['public_key'])
        )
        
        # 提交投票
        response = requests.post(
            f'{BASE_URL}/api/vote',
            json={
                'voter_id': credentials['voter_id'],
                'vote': 'A',
                'vote_proof': vote_proof,
                'identity_proof': identity_proof
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        print("提交投票成功")
        
        # 验证投票包含性
        response = requests.post(
            f'{BASE_URL}/api/verify-vote',
            json={'commitment': vote_proof['commitment']}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertTrue(response.json()['is_included'])
        print("验证投票包含性成功")
        
    def test_04_voting_restrictions(self):
        """测试投票限制"""
        print("\n=== 测试投票限制 ===")
        
        if 'voter2' not in self.test_credentials:
            self.skipTest("需要先完成投票流程测试")
            
        credentials = self.test_credentials['voter2']
        
        # 测试重复投票
        success, vote_prep = self.prepare_vote(
            credentials['voter_id'],
            'B',
            credentials['vote_randomness']
        )
        self.assertTrue(success)
        vote_proof = vote_prep['data']
        
        identity_proof = self.create_identity_proof(
            credentials['voter_id'],
            int(credentials['private_key']),
            int(credentials['public_key'])
        )
        
        response = requests.post(
            f'{BASE_URL}/api/vote',
            json={
                'voter_id': credentials['voter_id'],
                'vote': 'B',
                'vote_proof': vote_proof,
                'identity_proof': identity_proof
            }
        )
        self.assertNotEqual(response.status_code, 200)
        print("重复投票被正确阻止")
        
        # 结束投票
        response = requests.post(f'{BASE_URL}/api/end')
        self.assertEqual(response.status_code, 200)
        print("结束投票成功")
        
        # 测试在投票结束后投票
        success, response = self.register_voter('test_voter_3')
        self.assertTrue(success)
        credentials = response['data']
        
        success, vote_prep = self.prepare_vote(
            credentials['voter_id'],
            'A',
            credentials['vote_randomness']
        )
        self.assertTrue(success)
        vote_proof = vote_prep['data']
        
        identity_proof = self.create_identity_proof(
            credentials['voter_id'],
            int(credentials['private_key']),
            int(credentials['public_key'])
        )
        
        response = requests.post(
            f'{BASE_URL}/api/vote',
            json={
                'voter_id': credentials['voter_id'],
                'vote': 'A',
                'vote_proof': vote_proof,
                'identity_proof': identity_proof
            }
        )
        self.assertNotEqual(response.status_code, 200)
        print("投票结束后的投票被正确阻止")
        
    def test_05_results(self):
        """测试结果统计"""
        print("\n=== 测试结果统计 ===")
        
        response = requests.get(f'{BASE_URL}/api/results')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        results = data['data']
        
        # 验证结果格式
        self.assertIn('vote_counts', results)
        self.assertIn('total_votes', results)
        self.assertIn('voting_period', results)
        
        print("投票统计结果：")
        print(json.dumps(results, indent=2))

if __name__ == '__main__':
    try:
        print("开始API测试...")
        unittest.main(verbosity=2)
    except Exception as e:
        print("测试失败:", str(e))
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except requests.exceptions.ConnectionError:
        print("错误: 无法连接到服务器。请确保Flask应用正在运行。")