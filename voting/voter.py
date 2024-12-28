from typing import Dict, Optional, Tuple
from .zk_proof import ZKProof
import json
import time
from Crypto.Random import get_random_bytes

class VoterManager:
    def __init__(self):
        self.zk_proof = ZKProof()
        # 存储结构: voter_id -> {public_key, registration_time, vote_status}
        self.registered_voters = {}
        self.registered_voter_ids = set()
        # 存储已使用的承诺以防止重复投票
        self.used_commitments = set()
        # 存储已使用的公钥
        self.used_public_keys = set()
        
    def register_voter(self, voter_id: str) -> Dict:
        """
        注册新投票者
        返回包含必要凭证的字典
        """
        if voter_id in self.registered_voter_ids:
            raise ValueError("Voter ID already registered")
            
        try:
            # 生成投票者的密钥对,实际过程中在本地生成
            private_key, public_key = self.zk_proof.generate_keypair()
            
            # 检查公钥是否已被使用
            if public_key in self.used_public_keys:
                raise ValueError("Generated key pair collision. Please try again.")

            # 生成用于投票的随机值
            vote_randomness = int.from_bytes(get_random_bytes(32), 'big') % (self.zk_proof.p - 1)

            # 记录投票者信息
            self.registered_voters[public_key] = {
                'registration_time': int(time.time()),
                'vote_status': {
                    'has_voted': False,
                    'vote_time': None,
                    'vote_commitment': None
                }
            }
            
            self.used_public_keys.add(str(public_key))
            self.registered_voter_ids.add(voter_id)
            
            # 返回投票者需要保存的信息
            return {
                'voter_id': voter_id,
                'private_key': private_key,
                'public_key': public_key,
                'vote_randomness': vote_randomness
            }
            
        except Exception as e:
            if voter_id in self.registered_voters:
                del self.registered_voters[voter_id]
            raise Exception(f"Voter registration failed: {str(e)}")
    
    def verify_voter_identity(self, public_key: str, proof: Dict) -> bool:
        """验证投票者身份"""
        try:
            if public_key not in self.used_public_keys:
                print(self.used_public_keys)
                print(f"Voter {public_key} not found in registered voters")
                return False
                
            print(f"Verifying identity - public key: {public_key}")
            # 验证身份证明
            try:
                is_valid = self.zk_proof.verify_identity_proof(public_key,proof)
                print(f"Identity proof verification result: {is_valid}")
                return is_valid
            except Exception as e:
                print(f"Error during identity proof verification: {str(e)}")
                return False
                
        except Exception as e:
            print(f"Error during identity verification: {str(e)}")
            return False
    
    def process_vote(self, public_key: str, vote: str) -> bool:
        """
        处理投票请求
        验证投票的有效性并记录投票状态
        """
        try:
            voter_info = self.registered_voters[int(public_key)]
            
            if voter_info['vote_status']['has_voted']:
                raise ValueError("Voter has already voted")
                
            # print("Processing vote with proof:", json.dumps(vote_proof, indent=2))

            # 构造验证需要的数据格式
            # verification_data = {
            #     'commitment': vote_proof['commitment'],
            #     'proof_data': {
            #         'commitment': vote_proof['commitment'],
            #         'randomness': vote_proof['randomness']
            #     }
            # }
                
            # 验证投票承诺
            # if not self.zk_proof.verify_vote(vote, verification_data):
            #     raise ValueError("Invalid vote commitment")
                
            # 检查投票承诺是否已被使用
            # commitment_str = str(vote_proof['commitment'])
            # if commitment_str in self.used_commitments:
            #     raise ValueError("Vote commitment already used")
                
            # 记录投票状态
            current_time = int(time.time())
            voter_info['vote_status'].update({
                'has_voted': True,
                'vote_time': current_time,
                'vote_commitment': ""
            })
            
            # self.used_commitments.add()
            return True
            
        except Exception as e:
            print(f"Error in process_vote: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
        
    def get_voter_status(self, public_key: str) -> Optional[Dict]:
        """获取投票者状态"""
        public_key = int(public_key)
        voter_info = self.registered_voters[public_key]
        return {
            'registered': True,
            'registration_time': voter_info['registration_time'],
            'has_voted': voter_info['vote_status']['has_voted'],
            'vote_time': voter_info['vote_status']['vote_time']
        }