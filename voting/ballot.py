from collections import defaultdict
from typing import Dict, List, Optional
import time
import json  # 添加 json 模块导入
from .zk_proof import ZKProof

class BallotSystem:
    def __init__(self):
        self.zk_proof = ZKProof()
        # 存储结构改进：只存储已验证的投票承诺和投票选项
        self.ballots = []  # List[Dict] 存储 {commitment, vote, timestamp}
        self.vote_counts = defaultdict(int)
        self.voting_status = {
            'is_open': False,
            'start_time': None,
            'end_time': None,
            'total_votes': 0
        }
        # 存储用于验证的投票承诺
        self.vote_commitments = set()
        
    def start_voting(self, duration_seconds: int) -> Dict:
        """
        开始新的投票会话
        """
        try:
            if self.voting_status['is_open']:
                raise ValueError("Voting is already open")
                
            if duration_seconds <= 0:
                raise ValueError("Duration must be positive")
                
            current_time = time.time()
            self.voting_status.update({
                'is_open': True,
                'start_time': current_time,
                'end_time': current_time + duration_seconds,
                'total_votes': 0
            })
            
            # 清除之前的投票数据
            self.ballots.clear()
            self.vote_counts.clear()
            self.vote_commitments.clear()
            
            return {
                'status': 'success',
                'start_time': self.voting_status['start_time'],
                'end_time': self.voting_status['end_time']
            }
        except Exception as e:
            print(f"Error starting vote: {str(e)}")
            raise
        
    def end_voting(self) -> Dict:
        """
        结束当前投票会话
        """
        if not self.voting_status['is_open']:
            raise ValueError("Voting is not open")
            
        self.voting_status['is_open'] = False
        self.voting_status['end_time'] = time.time()
        
        return {
            'status': 'success',
            'total_votes': self.voting_status['total_votes'],
            'end_time': self.voting_status['end_time']
        }
        
    def submit_vote(self, vote: str) -> Dict:
        """提交匿名投票"""
        try:
            if not self.is_voting_open():
                raise ValueError("Voting is not open")
            
            # print("Received vote proof for verification:", json.dumps(vote_proof))
            
            # # 验证投票承诺是否已使用
            # commitment = vote_proof.get('commitment')
            # if not commitment:
            #     raise ValueError("Missing commitment in vote proof")
                
            # # 将commitment转换为字符串以确保一致性
            # commitment_str = str(commitment)
            
            # if commitment_str in self.vote_commitments:
            #     raise ValueError("Vote commitment already used")
            
            # # 构造验证所需的数据
            # verification_data = {
            #     'commitment': commitment_str,
            #     'proof_data': {
            #         'randomness': str(vote_proof.get('randomness', ''))
            #     }
            # }
            
            # print("Verifying vote with data:", json.dumps(verification_data))
            
            # # 验证投票的有效性
            # if not self.zk_proof.verify_vote(vote, verification_data):
            #     raise ValueError("Invalid vote verification")
            
            # 记录投票前保存当前状态
            commitment_str = ""
            current_time = time.time()
            try:
                # 记录投票
                ballot = {
                    'commitment': commitment_str,
                    'vote': vote,
                    'timestamp': current_time
                }
                
                # 更新所有计票相关的数据
                self.ballots.append(ballot)
                self.vote_counts[vote] += 1
                self.vote_commitments.add(commitment_str)
                self.voting_status['total_votes'] += 1
                
                return {
                    'status': 'success',
                    'timestamp': ballot['timestamp']
                }
                
            except Exception as e:
                # 如果在记录过程中出现错误，回滚所有更改
                if ballot in self.ballots:
                    self.ballots.remove(ballot)
                if vote in self.vote_counts:
                    self.vote_counts[vote] -= 1
                    if self.vote_counts[vote] <= 0:
                        del self.vote_counts[vote]
                if commitment_str in self.vote_commitments:
                    self.vote_commitments.remove(commitment_str)
                self.voting_status['total_votes'] = max(0, self.voting_status['total_votes'] - 1)
                raise
                
        except Exception as e:
            print(f"Vote submission error: {str(e)}")
            import traceback
            traceback.print_exc()
            raise ValueError(str(e))
        
    def get_results(self) -> Dict:
        """
        获取投票结果
        只在投票结束后可用
        """
        if self.is_voting_open():
            raise ValueError("Cannot get results while voting is open")
            
        results = {
            'vote_counts': dict(self.vote_counts),
            'total_votes': self.voting_status['total_votes'],
            'voting_period': {
                'start_time': self.voting_status['start_time'],
                'end_time': self.voting_status['end_time']
            }
        }
        
        # 添加百分比统计
        if self.voting_status['total_votes'] > 0:
            results['percentages'] = {
                option: (count / self.voting_status['total_votes']) * 100
                for option, count in self.vote_counts.items()
            }
            
        return results
        
    def get_current_status(self) -> Dict:
        """获取当前投票状态"""
        current_time = time.time()
        time_remaining = (
            max(0, self.voting_status.get('end_time', 0) - current_time)
            if self.voting_status.get('is_open', False) else 0
        )
        
        return {
            'is_open': self.voting_status.get('is_open', False),
            'total_votes': self.voting_status.get('total_votes', 0),
            'time_remaining': time_remaining,
            'start_time': self.voting_status.get('start_time'),
            'end_time': self.voting_status.get('end_time')
        }

    def is_voting_open(self) -> bool:
        """检查投票是否开放"""
        if not self.voting_status.get('is_open', False):
            return False
            
        current_time = time.time()
        if current_time > self.voting_status.get('end_time', 0):
            self.voting_status['is_open'] = False
            return False
            
        return True
        
    def verify_vote_inclusion(self, vote_commitment: int) -> bool:
        """
        验证特定投票是否被计入
        允许投票者验证自己的投票是否被正确记录
        """
        return vote_commitment in self.vote_commitments
        
    def get_voting_statistics(self) -> Dict:
        """
        获取详细的投票统计信息
        """
        total_votes = self.voting_status['total_votes']
        vote_distribution = {}
        
        if total_votes > 0:
            for option, count in self.vote_counts.items():
                vote_distribution[option] = {
                    'count': count,
                    'percentage': (count / total_votes) * 100
                }
                
        return {
            'total_votes': total_votes,
            'distribution': vote_distribution,
            'voting_duration': {
                'start_time': self.voting_status['start_time'],
                'end_time': self.voting_status['end_time'],
                'duration_minutes': (self.voting_status['end_time'] - 
                                  self.voting_status['start_time']) / 60
                if self.voting_status['end_time'] else None
            }
        }
    
    def get_current_status(self) -> Dict:
        """获取当前投票状态"""
        current_time = time.time()
        time_remaining = (
            max(0, self.voting_status['end_time'] - current_time)
            if self.voting_status['is_open'] else 0
        )
        
        return {
            'is_open': self.voting_status['is_open'],
            'total_votes': self.voting_status['total_votes'],
            'time_remaining': time_remaining,
            'voting_open': self.voting_status['is_open'],
            'start_time': self.voting_status['start_time'],
            'end_time': self.voting_status['end_time']
        }
    def rollback_vote(self, vote: str, vote_proof: Dict):
        """回滚一次投票"""
        try:
            commitment_str = str(vote_proof.get('commitment'))
            # 从投票记录中移除
            self.ballots = [b for b in self.ballots if b['commitment'] != commitment_str]
            
            # 更新计票
            if vote in self.vote_counts:
                self.vote_counts[vote] = max(0, self.vote_counts[vote] - 1)
                if self.vote_counts[vote] == 0:
                    del self.vote_counts[vote]
            
            # 移除已使用的承诺
            if commitment_str in self.vote_commitments:
                self.vote_commitments.remove(commitment_str)
            
            # 更新总票数
            self.voting_status['total_votes'] = max(0, self.voting_status['total_votes'] - 1)
            
        except Exception as e:
            print(f"Error during vote rollback: {str(e)}")
            import traceback
            traceback.print_exc()