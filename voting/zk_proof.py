from Crypto.Hash import SHA256
from Crypto.Random import get_random_bytes
import json
import time
from typing import Dict, Tuple

class ZKProof:
    def __init__(self):
        # 大素数，公开
        self.p = int('FFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD129024E088A67CC74'
                    '020BBEA63B139B22514A08798E3404DDEF9519B3CD3A431B302B0A6DF25F1437'
                    '4FE1356D6D51C245E485B576625E7EC6F44C42E9A637ED6B0BFF5CB6F406B7ED'
                    'EE386BFB5A899FA5AE9F24117C4B1FE649286651ECE45B3DC2007CB8A163BF05'
                    '98DA48361C55D39A69163FA8FD24CF5F83655D23DCA3AD961C62F356208552BB'
                    '9ED529077096966D670C354E4ABC9804F1746C08CA18217C32905E462E36CE3B'
                    'E39E772C180E86039B2783A2EC07A28FB5C55DF06F4C52C9DE2BCBF695581718'
                    '3995497CEA956AE515D2261898FA051015728E5A8AACAA68FFFFFFFFFFFFFFFF', 16)
        # 生成元，公开
        self.g = 2
        # 投票选项到数值的映射
        self.vote_options = {'A': 1, 'B': 2, 'C': 3}
        
    def generate_keypair(self) -> Tuple[int, int]:
        """生成投票者的密钥对，实际场景中在本地进行"""
        # 私钥是一个随机数
        private_key = int.from_bytes(get_random_bytes(32), 'big') % (self.p - 1)
        # 公钥是 g^private_key mod p
        public_key = pow(self.g, private_key, self.p)
        return private_key, public_key

    def generate_registration_commitment(self, randomness: int) -> int:
        """
        生成注册阶段的承诺
        这个承诺仅用于注册阶段，与投票承诺分开
        """
        if not 0 <= randomness < self.p:
            raise ValueError("randomness must be in range [0, p)")

        # 使用 voter_id 和随机数创建承诺
        commitment = pow(self.g, randomness, self.p)
        
        return commitment
        
    def create_vote_commitment(self, vote: str, randomness: int) -> Tuple[int, Dict]:
        """创建投票承诺"""
        if vote not in self.vote_options:
            raise ValueError("Invalid vote option")
        
        # 将投票选项转换为数值
        vote_value = self.vote_options[vote]
        
        # 计算投票承诺: g^vote * h^randomness mod p
        # 这里使用 g^randomness 作为 h
        h = pow(self.g, randomness, self.p)
        commitment = (pow(self.g, vote_value, self.p) * h) % self.p
        
        # 保存用于验证的信息
        proof_data = {
            'commitment': commitment,
            'randomness': randomness
        }
        
        return commitment, proof_data
    
    def create_challenge(self , public_key: str, commitment:str) -> Dict:
        """
        创建证明身份的零知识证明（Schnorr协议）
        """
        try:
            # 转换输入的字符串为整数
            public_key_int = int(public_key)
            
            # 创建挑战
            message = str(public_key_int).encode() + str(commitment).encode()
            challenge = int(SHA256.new(message).hexdigest(), 16) % (self.p - 1)
            
            # 计算响应
            # response = (k + challenge * private_key_int) % (self.p - 1)
            
            # print(f"Debug - Identity Proof: public_key={public_key_int}, r={r}, response={response}")
            
            return {
                'challenge': str(challenge),
            }
        except Exception as e:
            print(f"Error in create_challenge: {str(e)}")
            raise
    
    def verify_identity_proof(self, public_key:str,proof: Dict) -> bool:
        """验证身份证明"""
        try:
            # 转换所有输入为整数
            # response public_key challenge commitment
            commitment = int(proof['commitment'])
            response = int(proof['response'])
            public_key = int(public_key)
            
            # 重构挑战
            message = str(public_key).encode() + str(commitment).encode()
            challenge = int(SHA256.new(message).hexdigest(), 16) % (self.p - 1)
            
            # 验证等式: g^response = r * (public_key)^challenge mod p
            left_side = pow(self.g, response, self.p)
            right_side = (commitment * pow(public_key, challenge, self.p)) % self.p
            
            result = left_side == right_side
            print(f"Verify identity proof - Result: {result}")
            print(f"Verify identity proof - Left side: {left_side}")
            print(f"Verify identity proof - Right side: {right_side}")
            
            return result
        except Exception as e:
            print(f"Verification failed: {str(e)}")
            return False

    def verify_vote(self, vote: str, proof_data: Dict) -> bool:
        """验证投票的有效性"""
        try:
            print("\nVerify vote details:")
            print(f"Vote option: {vote}")
            print(f"Proof data: {json.dumps(proof_data, indent=2)}")
            
            if vote not in self.vote_options:
                print(f"Invalid vote option: {vote}")
                return False
                
            vote_value = self.vote_options[vote]
            print(f"Vote value: {vote_value}")
            
            # 从proof_data中获取commitment和randomness
            try:
                commitment = str(proof_data.get('commitment', ''))
                randomness = proof_data.get('proof_data', {}).get('randomness', '')
                
                print(f"Extracted commitment: {commitment}")
                print(f"Extracted randomness: {randomness}")
                
                if not commitment or not randomness:
                    print("Missing required proof data")
                    return False
                    
                commitment = int(commitment)
                randomness = int(str(randomness))
                
                print(f"Converted values:")
                print(f"Commitment (int): {commitment}")
                print(f"Randomness (int): {randomness}")
                
                # 计算预期的承诺值
                h = pow(self.g, randomness, self.p)
                expected_commitment = (pow(self.g, vote_value, self.p) * h) % self.p
                
                print(f"Calculated values:")
                print(f"g^vote mod p: {pow(self.g, vote_value, self.p)}")
                print(f"h = g^randomness mod p: {h}")
                print(f"Expected commitment: {expected_commitment}")
                print(f"Actual commitment: {commitment}")
                
                result = expected_commitment == commitment
                print(f"Verification result: {result}")
                
                return result
                
            except (ValueError, TypeError) as e:
                print(f"Error converting values: {e}")
                return False
                
        except Exception as e:
            print(f"Vote verification failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
            
    def create_double_voting_prevention_proof(self, private_key: int, vote_hash: str) -> Dict:
        """创建防止重复投票的证明"""
        # 使用私钥签名投票哈希
        message = int(vote_hash, 16) % (self.p - 1)
        signature = pow(message, private_key, self.p)
        
        return {
            'vote_hash': vote_hash,
            'signature': signature
        }
    
    def verify_double_voting_prevention_proof(self, proof: Dict, public_key: int) -> bool:
        """验证防重复投票证明"""
        try:
            message = int(proof['vote_hash'], 16) % (self.p - 1)
            verification = pow(proof['signature'], public_key, self.p)
            return verification == message
        except Exception as e:
            print(f"Double voting prevention proof verification failed: {str(e)}")
            return False
        
    def calculate_response(self, random_val: int, challenge: int, private_key: int) -> int:
        """
        根据 Schnorr 协议计算响应值:
        s = (k + e * x) mod (p - 1)

        :param random_val: k, 随机数
        :param challenge: e, 挑战值
        :param private_key: x, 私钥
        :return: s, 响应值
        """
        # 计算 s
        response = (random_val + challenge * private_key) % (self.p - 1)
        return response