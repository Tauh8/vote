from flask import Flask, request, jsonify, render_template
from voting.zk_proof import ZKProof
from voting.voter import VoterManager
from voting.ballot import BallotSystem
import time
import json  # 添加这行
from threading import Lock

app = Flask(__name__)

# 初始化系统组件
zk_proof = ZKProof()
voter_manager = VoterManager()
ballot_system = BallotSystem()
lock = Lock()

@app.route('/')
def index():
    """渲染主页"""
    return render_template('index.html')

@app.route('/api/register', methods=['POST'])
def register():
    """
    注册新投票者
    请求数据：{ voter_id: string }
    实际环境中，服务器不会知道private_key和randomness，这里为了简化前端实现，在后端生成了private_key和public_key
    """
    with lock:
        try:
            data = request.get_json()
            voter_id = data.get('voter_id')
            
            if not voter_id:
                return jsonify({
                    'success': False,
                    'error': 'Voter ID is required.'
                }), 400

            # 注册新投票者并获取凭证
            credentials = voter_manager.register_voter(voter_id)
            
            # 使用 voter_id 和 vote_randomness 生成注册承诺
            commitment = zk_proof.generate_registration_commitment(
                credentials['vote_randomness']
            )
            
            # 合并所有需要返回的信息，
            response_data = {
                'voter_id': credentials['voter_id'],
                'private_key': str(credentials['private_key']), # 在实际环境中，服务器不会知道private_key
                'public_key': str(credentials['public_key']), # 在实际环境中，服务器知道public_key
                'vote_randomness': str(credentials['vote_randomness']), # 在实际环境中，服务器不会知道vote_randomness
                'commitment': str(commitment) # 在实际环境中，commitment也是在本地生成的
            }
            
            return jsonify({
                'success': True,
                'data': response_data
            })
            
        except ValueError as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Registration failed: {str(e)}'
            }), 500

@app.route('/api/cal-res', methods=['POST'])
def cal_res():
    """
    计算响应
    请求数据：{ 
        random_val: string,
        challenge: string,
        private_key: string
    }
    """
    try:
        data = request.get_json()
        random_val = int(data.get('random_val'))
        challenge = int(data.get('challenge'))
        private_key = int(data.get('private_key'))     
        response = zk_proof.calculate_response(random_val, challenge, private_key)

        return jsonify({
            'success': True,
            'data': {
                'response': response,
                'timestamp': time.time()
            }   
        })        
    except Exception as e:       
        return jsonify({
            'success': False,
            'error': f'Cal res failed: {str(e)}'
        }), 500

@app.route('/api/verify-identity', methods=['POST'])
def verify_identity():
    """
    验证投票者身份
    请求数据：{ 
        public_key: string,
        proof: object
    }
    """
    try:
        data = request.get_json()
        public_key = data.get('public_key')
        proof = data.get('proof')
        
        if not public_key or not proof:
            return jsonify({
                'success': False,
                'error': 'public_key and identity proof are required.'
            }), 400

        # 验证身份
        is_valid = voter_manager.verify_voter_identity(public_key, proof)
        if(not is_valid):
            return jsonify({
                'success': False,
                'error': 'Invalid identity proof.'
            }), 400
        
        return jsonify({
            'success': True,
            'data': {
                'is_valid': is_valid,
                'timestamp': time.time()
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Identity verification failed: {str(e)}'
        }), 500

# @app.route('/api/prepare-vote', methods=['POST'])
# def prepare_vote():
#     """
#     生成投票承诺
#     """
#     try:
#         data = request.get_json()
#         print("\nReceived prepare vote request:", json.dumps(data, indent=2))
        
#         voter_id = data.get('voter_id')
#         vote = data.get('vote')
#         vote_randomness = int(data.get('vote_randomness'))
        
#         if not all([voter_id, vote, vote_randomness]):
#             return jsonify({
#                 'success': False,
#                 'error': 'Missing required parameters.'
#             }), 400

#         # 创建投票承诺
#         commitment, proof_data = zk_proof.create_vote_commitment(vote, vote_randomness)
        
#         # 准备返回数据
#         response_data = {
#             'commitment': str(commitment),
#             'proof_data': {
#                 'commitment': str(commitment),
#                 'randomness': str(vote_randomness)
#             }
#         }
        
#         print("Prepared vote data:", json.dumps(response_data, indent=2))
        
#         return jsonify({
#             'success': True,
#             'data': response_data
#         })
        
#     except Exception as e:
#         print(f"Vote preparation failed: {str(e)}")
#         import traceback
#         traceback.print_exc()
#         return jsonify({
#             'success': False,
#             'error': f'Vote preparation failed: {str(e)}'
#         }), 500

# @app.route('/api/generate-proof', methods=['POST'])
# def generate_proof():
#     """生成身份证明"""
#     try:
#         data = request.get_json()
#         print("Received proof generation data:", data)  # 添加日志
        
#         voter_id = data.get('voter_id')
#         private_key = str(data.get('private_key'))  # 转换为字符串
#         public_key = str(data.get('public_key'))    # 转换为字符串
        
#         if not all([voter_id, private_key, public_key]):
#             return jsonify({
#                 'success': False,
#                 'error': 'Missing required parameters.'
#             }), 400

#         # 创建挑战
#         identity_proof = zk_proof.create_challenge(
#             private_key=private_key,
#             public_key=public_key
#         )
        
#         # 添加调试日志
#         print("Generated identity proof:", identity_proof)
        
#         return jsonify({
#             'success': True,
#             'data': identity_proof
#         })
#     except Exception as e:
#         print(f"Proof generation error: {str(e)}")  # 添加错误日志
#         return jsonify({
#             'success': False,
#             'error': f'Failed to generate proof: {str(e)}'
#         }), 500

@app.route('/api/vote', methods=['POST'])
def vote():
    """
    提交投票
    """
    with lock:
        try:
            data = request.get_json()
            print("\nReceived vote request data:", json.dumps(data, indent=2))
            
            # voter_id = data.get('voter_id')
            vote = data.get('vote')
            # vote_proof = data.get('vote_proof')
            identity_proof = data.get('identity_proof')
            public_key = str(data.get('public_key'))
            
            if not all([vote, identity_proof, public_key]):
                missing = [k for k in ['vote', 'identity_proof', 'public_key'] 
                          if not data.get(k)]
                return jsonify({
                    'success': False,
                    'error': f'Missing required parameters: {", ".join(missing)}'
                }), 400

            # 先验证身份
            print("\nVerifying voter identity...")
            try:
                # print("Identity proof:", identity_proof["proof"])
                is_valid = voter_manager.verify_voter_identity(public_key, identity_proof["proof"])
                if not is_valid:
                    return jsonify({
                        'success': False,
                        'error': 'Invalid voter identity.'
                    }), 401
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': f'Identity verification failed: {str(e)}'
                }), 401

            try:
                # 验证投票者状态
                voter_status = voter_manager.get_voter_status(public_key)
                if voter_status and voter_status.get('has_voted'):
                    return jsonify({
                        'success': False,
                        'error': 'Voter has already voted.'
                    }), 400

                # 处理投票
                print("\nProcessing vote...")
                vote_result = ballot_system.submit_vote(vote)

                # 只有在投票成功后才更新选民状态
                try:
                    voter_manager.process_vote(public_key, vote)
                except Exception as e:
                    # 如果更新选民状态失败，需要回滚投票
                    # ballot_system.rollback_vote(vote, vote_proof)
                    raise

                return jsonify({
                    'success': True,
                    'data': vote_result
                })
                
            except ValueError as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 400
            
        except Exception as e:
            print(f"\nVote submission error: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
        
@app.route('/api/end', methods=['POST'])
def end_voting():
    """结束投票会话"""
    with lock:
        try:
            result = ballot_system.end_voting()
            return jsonify({
                'success': True,
                'data': result
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Failed to end voting: {str(e)}'
            }), 500

@app.route('/api/request-challenge', methods=['POST'])
def request_challenge():
    """
    请求登录挑战
    请求数据：{ 
        public_key: string,
        R: string  // 承诺值
    }
    """
    try:
        data = request.get_json()
        public_key = data.get('public_key')
        commitment = int(data.get('commitment'))  # 前端发送的承诺值

        if not public_key or not commitment:
            return jsonify({
                'success': False,
                'error': 'Missing required parameters'
            }), 400

        # 生成挑战值
        challenge = zk_proof.create_challenge(public_key, commitment)

        print(f"Challenge generated for public key {public_key}: {challenge}")

        return jsonify({
            'success': True,
            'data': {
                'challenge': challenge
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to generate challenge: {str(e)}'
        }), 500

# @app.route('/api/verify-login', methods=['POST'])
# def verify_login():
#     """
#     验证登录证明
#     请求数据：{
#         public_key: string,
#         proof: {
#             R: string,  // 承诺值
#             s: string   // 证明值
#         }
#     }
#     """
#     try:
#         data = request.get_json()
#         public_key = data.get('public_key')
#         proof = data.get('proof', {})
#         R = int(proof.get('commitment'))
#         s = int(proof.get('s'))

#         if not all([public_key, R, s]):
#             return jsonify({
#                 'success': False,
#                 'error': 'Missing required parameters'
#             }), 400


#         if is_valid:
#             # 登录成功，生成会话令牌
#             token = generate_session_token()  # 需要实现这个函数
#             return jsonify({
#                 'success': True,
#                 'data': {
#                     'token': token,
#                     'timestamp': time.time()
#                 }
#             })
#         else:
#             raise ValueError('Invalid proof')

#     except ValueError as e:
#         return jsonify({
#             'success': False,
#             'error': str(e)
#         }), 401
#     except Exception as e:
#         return jsonify({
#             'success': False,
#             'error': f'Login verification failed: {str(e)}'
#         }), 500

# def generate_session_token():
#     """生成会话令牌"""
#     import secrets
#     return secrets.token_urlsafe(32)  # 生成一个随机的会话令牌


@app.route('/api/results', methods=['GET'])
def results():
    """获取投票结果"""
    try:
        # 使用 get_current_status 替代直接检查 is_open
        current_status = ballot_system.get_current_status()
        if not current_status['is_open']:
            return jsonify({
                'success': True,
                'data': {
                    'results': {},
                    'statistics': current_status
                }
            })
            
        results = {
            'results': ballot_system.vote_counts,
            'statistics': current_status
        }
        return jsonify({
            'success': True,
            'data': results
        })
    except Exception as e:
        print(f"Error in results: {str(e)}")  # 添加日志
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    """获取当前投票状态"""
    try:
        status = ballot_system.get_current_status()
        return jsonify({
            'success': True,
            'data': status
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get status: {str(e)}'
        }), 500

@app.route('/api/verify-vote', methods=['POST'])
def verify_vote():
    """
    验证投票是否被计入
    请求数据：{ commitment: string }
    """
    try:
        data = request.get_json()
        commitment = int(data.get('commitment'))
        
        is_included = ballot_system.verify_vote_inclusion(commitment)
        
        return jsonify({
            'success': True,
            'is_included': is_included
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Vote verification failed: {str(e)}'
        }), 500

def voting_timer():
    """投票计时器，自动结束超时的投票会话"""
    while True:
        time.sleep(1)
        with lock:
            try:
                current_status = ballot_system.get_current_status()
                if current_status['is_open'] and current_status['time_remaining'] <= 0:
                    try:
                        ballot_system.end_voting()
                        print("Voting session ended automatically.")
                    except Exception as e:
                        print(f"Failed to end voting session: {str(e)}")
            except Exception as e:
                print(f"Error in voting timer: {str(e)}")

@app.route('/api/start', methods=['POST'])
def start_voting():
    """开始投票会话"""
    with lock:
        try:
            data = request.get_json()
            duration = data.get('duration', 60)  # 默认60秒
            
            result = ballot_system.start_voting(duration)
            
            return jsonify({
                'success': True,
                'data': result
            })
            
        except ValueError as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Failed to start voting: {str(e)}'
            }), 500
        
if __name__ == '__main__':
    from threading import Thread
    timer_thread = Thread(target=voting_timer, daemon=True)
    timer_thread.start()
    app.run(host='0.0.0.0', port=5000, debug=True)