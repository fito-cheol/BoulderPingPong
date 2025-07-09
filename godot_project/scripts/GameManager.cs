using Godot;
using System;
using System.Collections.Generic;
using Godot.Collections;

public partial class GameManager : Node
{
	[Signal]
	public delegate void GameStartedEventHandler();
	
	[Signal]
	public delegate void GameEndedEventHandler();
	
	[Signal]
	public delegate void ScoreUpdatedEventHandler(int playerScore, int aiScore);

	[Export]
	public Node PoseReceiver { get; set; }
	
	[Export]
	public Node2D Ball { get; set; }
	
	[Export]
	public Node2D PlayerPaddle1 { get; set; }  // 왼쪽 손
	[Export]
	public Node2D PlayerPaddle2 { get; set; }  // 오른쪽 손
	[Export]
	public Node2D PlayerPaddle3 { get; set; }  // 왼쪽 발
	[Export]
	public Node2D PlayerPaddle4 { get; set; }  // 오른쪽 발
	
	[Export]
	public Node2D AIPaddle { get; set; }
	
	[Export]
	public Label ScoreLabel { get; set; }
	
	[Export]
	public Label StatusLabel { get; set; }

	[Export]
	public Label DebugLabel { get; set; }
 
	// 게임 설정
	private float gameWidth = 1920.0f;
	private float gameHeight = 1080.0f;
	private float ballSpeed = 400.0f;
	private float paddleSpeed = 300.0f;
	private float aiSpeed = 250.0f;

	// 게임 상태
	private bool gameActive = false;
	private int playerScore = 0;
	private int aiScore = 0;
	private Vector2 ballVelocity = Vector2.Zero;

	// 포즈 데이터 처리
	private List<Godot.Collections.Dictionary> playerHands = new List<Godot.Collections.Dictionary>();
	private List<Godot.Collections.Dictionary> playerFeet = new List<Godot.Collections.Dictionary>();
	private double lastPoseTime = 0.0;
	private double poseTimeout = 5.0; // 5초 동안 포즈가 없으면 게임 일시정지

	private int playerCount = 0;
	private bool serverConnected = false;
	
	// 4개의 패들 포인트
	private Vector2 paddle1Target = Vector2.Zero;  // 왼쪽 손
	private Vector2 paddle2Target = Vector2.Zero;  // 오른쪽 손
	private Vector2 paddle3Target = Vector2.Zero;  // 왼쪽 발
	private Vector2 paddle4Target = Vector2.Zero;  // 오른쪽 발

	public override void _Ready()
	{
		//make this deferred ready
		CallDeferred(nameof(DeferredReady));
	}

	public void DeferredReady()
	{ 
		// 포즈 데이터 수신 연결
		if (PoseReceiver != null)
		{ 
			Signals.onPoseDataReceived += (pose_data) => OnPoseDataReceived(pose_data);
			//debug
			GD.Print("[GameManager] PoseDataReceiver -> GameManager 연결 완료");
		}
		
		// 게임 초기화
		InitializeGame();
			
		GD.Print("[GameManager] 초기화 완료");
	}

	public override void _Process(double delta)
	{
		if (!gameActive)
			return;
		
		// 포즈 데이터 타임아웃 체크
		if (Time.GetUnixTimeFromSystem() - lastPoseTime > poseTimeout)
		{
			StatusLabel.Text = "플레이어를 찾을 수 없습니다...";
			playerCount = 0;
			UpdateDebugStatus();
			return;
		}
		
		StatusLabel.Text = "게임 진행 중";
		UpdateDebugStatus();
		
		// 게임 업데이트
		UpdateBall((float)delta);
		UpdateAIPaddle((float)delta);
		CheckCollisions();
	}

	private void InitializeGame()
	{
		// 게임 요소 초기화
		Ball.Position = new Vector2(gameWidth / 2.0f, gameHeight / 2.0f);
		ballVelocity = new Vector2(ballSpeed, 0).Rotated((float)GD.RandRange(0.785f, 0.785f)); // Pi/4 radians   
		GD.Print("[GameManager] ballVelocity: ", ballVelocity);
		PlayerPaddle1.Position = new Vector2(100.0f, gameHeight / 2.0f);
		PlayerPaddle2.Position = new Vector2(gameWidth - 100.0f, gameHeight / 2.0f);
		AIPaddle.Position = new Vector2(gameWidth / 2.0f, gameHeight / 2.0f);
		
		UpdateScoreDisplay();
		gameActive = true;
		EmitSignal(nameof(GameStarted));
	} 
	private void OnPoseDataReceived(Dictionary poseData)
	{
		GD.Print("[GameManager] OnPoseDataReceived 호출됨");
		
		// null 체크 추가
		if (poseData == null)
		{
			GD.Print("[GameManager] poseData가 null입니다.");
			return;
		}
		
		GD.Print($"[GameManager] poseData 타입: {poseData.GetType()}");
		
		lastPoseTime = Time.GetUnixTimeFromSystem(); 
		
		// 디버그 프린트 문자 수 줄이기
		string jsonStr = Json.Stringify(poseData);
		if (jsonStr.Length > 200)
			jsonStr = jsonStr.Substring(0, 200) + "...";
		GD.Print($"[GameManager] 포즈 데이터 수신: {jsonStr}");
		GD.Print($"[GameManager] 포즈 데이터 키들: {string.Join(", ", poseData.Keys)}");
		
		if (poseData.ContainsKey("players"))
		{
			var playersVariant = poseData["players"];
			GD.Print($"[GameManager] playersVariant 타입: {playersVariant.VariantType}");
			
			if (playersVariant.VariantType == Variant.Type.Array)
			{
				var players = playersVariant.AsGodotArray();
				playerCount = players.Count;
				serverConnected = true;
				GD.Print($"[GameManager] 플레이어 수: {playerCount}");
				
				if (players.Count > 0)
				{
					var playerVariant = players[0];
					GD.Print($"[GameManager] playerVariant 타입: {playerVariant.VariantType}");
					
					if (playerVariant.VariantType == Variant.Type.Dictionary)
					{
						var player = playerVariant.AsGodotDictionary();
						// 디버그 프린트 문자 수 줄이기
						string playerJsonStr = Json.Stringify(player);
						if (playerJsonStr.Length > 200)
							playerJsonStr = playerJsonStr.Substring(0, 200) + "...";
						GD.Print($"[GameManager] 플레이어 데이터: {playerJsonStr}");
						GD.Print($"[GameManager] 플레이어 키들: {string.Join(", ", player.Keys)}");
						
						// 손과 발 데이터 추출
						playerHands.Clear();
						playerFeet.Clear();
						
						if (player.ContainsKey("hands"))
						{
							var handsVariant = player["hands"];
							GD.Print($"[GameManager] handsVariant 타입: {handsVariant.VariantType}");
							
							if (handsVariant.VariantType == Variant.Type.Array)
							{
								var hands = handsVariant.AsGodotArray();
								GD.Print($"[GameManager] 손 데이터 개수: {hands.Count}");
								foreach (var hand in hands)
								{
									GD.Print($"[GameManager] hand 타입: {hand.VariantType}");
									if (hand.VariantType == Variant.Type.Dictionary)
									{
										var handDict = hand.AsGodotDictionary();
										// 디버그 프린트 문자 수 줄이기
										string handJsonStr = Json.Stringify(handDict);
										if (handJsonStr.Length > 100)
											handJsonStr = handJsonStr.Substring(0, 100) + "...";
										GD.Print($"[GameManager] 손 데이터: {handJsonStr}");
										
										// 필수 필드 확인
										if (handDict.ContainsKey("x") && handDict.ContainsKey("y"))
										{
											// 안전한 float 변환
											float x = 0.0f, y = 0.0f, visibility = 1.0f, presence = 1.0f;
											
											try
											{
												x = handDict["x"].AsSingle();
												y = handDict["y"].AsSingle();
												
												if (handDict.ContainsKey("visibility"))
													visibility = handDict["visibility"].AsSingle();
												if (handDict.ContainsKey("presence"))
													presence = handDict["presence"].AsSingle();
											}
											catch (Exception e)
											{
												GD.Print($"[GameManager] 손 데이터 변환 오류: {e}");
												continue;
											}
											
											// visibility가 0.1 이상인 경우만 유효한 데이터로 간주
											if (visibility > 0.1f)
											{
												playerHands.Add(handDict);
												GD.Print($"[GameManager] 유효한 손 데이터 추가: visibility={visibility:F3}, presence={presence:F3}");
											}
											else
											{
												GD.Print($"[GameManager] 손 데이터 제외 (visibility 낮음): {visibility:F3}");
											}
										}
									}
								}
							}
						}
						else
						{
							GD.Print("[GameManager] 플레이어 데이터에 'hands' 키가 없음");
						}
						
						if (player.ContainsKey("feet"))
						{
							var feetVariant = player["feet"];
							GD.Print($"[GameManager] feetVariant 타입: {feetVariant.VariantType}");
							
							if (feetVariant.VariantType == Variant.Type.Array)
							{
								var feet = feetVariant.AsGodotArray();
								GD.Print($"[GameManager] 발 데이터 개수: {feet.Count}");
								foreach (var foot in feet)
								{
									GD.Print($"[GameManager] foot 타입: {foot.VariantType}");
									if (foot.VariantType == Variant.Type.Dictionary)
									{
										var footDict = foot.AsGodotDictionary();
										// 디버그 프린트 문자 수 줄이기
										string footJsonStr = Json.Stringify(footDict);
										if (footJsonStr.Length > 100)
											footJsonStr = footJsonStr.Substring(0, 100) + "...";
										GD.Print($"[GameManager] 발 데이터: {footJsonStr}");
										
										if (footDict.ContainsKey("x") && footDict.ContainsKey("y"))
										{
											// 안전한 float 변환
											float x = 0.0f, y = 0.0f, visibility = 1.0f, presence = 1.0f;
											
											try
											{
												x = footDict["x"].AsSingle();
												y = footDict["y"].AsSingle();
												
												if (footDict.ContainsKey("visibility"))
													visibility = footDict["visibility"].AsSingle();
												if (footDict.ContainsKey("presence"))
													presence = footDict["presence"].AsSingle();
											}
											catch (Exception e)
											{
												GD.Print($"[GameManager] 발 데이터 변환 오류: {e}");
												continue;
											}
											
											// visibility가 0.05 이상인 경우만 유효한 데이터로 간주
											if (visibility > 0.05f)
											{
												playerFeet.Add(footDict);
												GD.Print($"[GameManager] 유효한 발 데이터 추가: visibility={visibility:F3}, presence={presence:F3}");
											}
											else
											{
												GD.Print($"[GameManager] 발 데이터 제외 (visibility 낮음): {visibility:F3}");
											}
										}
									}
								}
							}
						}
						else
						{
							GD.Print("[GameManager] 플레이어 데이터에 'feet' 키가 없음");
						}
						
						// 플레이어 패들 업데이트
						UpdatePlayerPaddle();
					}
					else
					{
						GD.Print($"[GameManager] playerVariant가 Dictionary가 아님: {playerVariant.VariantType}");
					}
				}
				else
				{
					GD.Print("[GameManager] 플레이어 배열이 비어있음");
				}
				UpdateDebugStatus();
			}
			else
			{
				GD.Print($"[GameManager] playersVariant가 Array가 아님: {playersVariant.VariantType}");
				playerCount = 0;
				serverConnected = true;
				UpdateDebugStatus();
			}
		}
		else
		{
			GD.Print("[GameManager] 포즈 데이터에 'players' 키가 없음");
			playerCount = 0;
			serverConnected = true;
			UpdateDebugStatus();
		}
	}

	private void UpdatePlayerPaddle()
	{
		GD.Print($"[GameManager] UpdatePlayerPaddle 호출됨. 손 개수: {playerHands.Count}, 발 개수: {playerFeet.Count}");
		
		// 왼쪽/오른쪽 손과 발 데이터 분리
		var leftHand = new Godot.Collections.Dictionary();
		var rightHand = new Godot.Collections.Dictionary();
		var leftFoot = new Godot.Collections.Dictionary();
		var rightFoot = new Godot.Collections.Dictionary();
		
		// 손 데이터 분리 (왼쪽/오른쪽 구분)
		foreach (var hand in playerHands)
		{
			if (hand.ContainsKey("visibility") && hand.ContainsKey("x") && hand.ContainsKey("y") && hand.ContainsKey("side"))
			{
				try
				{
					float visibility = hand["visibility"].AsSingle();
					string side = hand["side"].AsString();
					
					if (visibility > 0.1f)  // 최소 visibility 기준
					{
						if (side == "left" && (leftHand.Count == 0 || visibility > leftHand["visibility"].AsSingle()))
						{
							leftHand = hand;
						}
						else if (side == "right" && (rightHand.Count == 0 || visibility > rightHand["visibility"].AsSingle()))
						{
							rightHand = hand;
						}
					}
				}
				catch (Exception e)
				{
					GD.Print($"[GameManager] 손 데이터 처리 오류: {e}");
				}
			}
		}
		
		// 발 데이터 분리 (왼쪽/오른쪽 구분)
		foreach (var foot in playerFeet)
		{
			if (foot.ContainsKey("visibility") && foot.ContainsKey("x") && foot.ContainsKey("y") && foot.ContainsKey("side"))
			{
				try
				{
					float visibility = foot["visibility"].AsSingle();
					string side = foot["side"].AsString();
					
					if (visibility > 0.05f)  // 최소 visibility 기준
					{
						if (side == "left" && (leftFoot.Count == 0 || visibility > leftFoot["visibility"].AsSingle()))
						{
							leftFoot = foot;
						}
						else if (side == "right" && (rightFoot.Count == 0 || visibility > rightFoot["visibility"].AsSingle()))
						{
							rightFoot = foot;
						}
					}
				}
				catch (Exception e)
				{
					GD.Print($"[GameManager] 발 데이터 처리 오류: {e}");
				}
			}
		}
		
		GD.Print($"[GameManager] 왼쪽 손: {leftHand.Count > 0}, 오른쪽 손: {rightHand.Count > 0}, 왼쪽 발: {leftFoot.Count > 0}, 오른쪽 발: {rightFoot.Count > 0}");
		
		// 패들 1 (왼쪽 손)
		if (leftHand.Count > 0)
		{
			try
			{
				float cameraX = leftHand["x"].AsSingle();
				float cameraY = leftHand["y"].AsSingle();
				
				// 좌표 클램핑
				cameraX = Mathf.Clamp(cameraX, 0.0f, 1.0f);
				cameraY = Mathf.Clamp(cameraY, 0.0f, 1.0f);
				
				// 카메라 좌표를 게임 좌표로 변환 (상하반전 수정)
				float gameX = cameraX * gameWidth;
				float gameY = cameraY * gameHeight;  // 상하반전 제거
				
				paddle1Target = new Vector2(gameX, gameY);
				GD.Print($"[GameManager] 패들1 (왼쪽 손) 목표: {paddle1Target}");
			}
			catch (Exception e)
			{
				GD.Print($"[GameManager] 패들1 좌표 변환 오류: {e}");
			}
		}
		
		// 패들 2 (오른쪽 손)
		if (rightHand.Count > 0)
		{
			try
			{
				float cameraX = rightHand["x"].AsSingle();
				float cameraY = rightHand["y"].AsSingle();
				
				// 좌표 클램핑
				cameraX = Mathf.Clamp(cameraX, 0.0f, 1.0f);
				cameraY = Mathf.Clamp(cameraY, 0.0f, 1.0f);
				
				// 카메라 좌표를 게임 좌표로 변환 (상하반전 수정)
				float gameX = cameraX * gameWidth;
				float gameY = cameraY * gameHeight;  // 상하반전 제거
				
				paddle2Target = new Vector2(gameX, gameY);
				GD.Print($"[GameManager] 패들2 (오른쪽 손) 목표: {paddle2Target}");
			}
			catch (Exception e)
			{
				GD.Print($"[GameManager] 패들2 좌표 변환 오류: {e}");
			}
		}
		
		// 패들 3 (왼쪽 발)
		if (leftFoot.Count > 0)
		{
			try
			{
				float cameraX = leftFoot["x"].AsSingle();
				float cameraY = leftFoot["y"].AsSingle();
				
				// 좌표 클램핑
				cameraX = Mathf.Clamp(cameraX, 0.0f, 1.0f);
				cameraY = Mathf.Clamp(cameraY, 0.0f, 1.0f);
				
				// 카메라 좌표를 게임 좌표로 변환 (상하반전 수정)
				float gameX = cameraX * gameWidth;
				float gameY = cameraY * gameHeight;  // 상하반전 제거
				
				paddle3Target = new Vector2(gameX, gameY);
				GD.Print($"[GameManager] 패들3 (왼쪽 발) 목표: {paddle3Target}");
			}
			catch (Exception e)
			{
				GD.Print($"[GameManager] 패들3 좌표 변환 오류: {e}");
			}
		}
		
		// 패들 4 (오른쪽 발)
		if (rightFoot.Count > 0)
		{
			try
			{
				float cameraX = rightFoot["x"].AsSingle();
				float cameraY = rightFoot["y"].AsSingle();
				
				// 좌표 클램핑
				cameraX = Mathf.Clamp(cameraX, 0.0f, 1.0f);
				cameraY = Mathf.Clamp(cameraY, 0.0f, 1.0f);
				
				// 카메라 좌표를 게임 좌표로 변환 (상하반전 수정)
				float gameX = cameraX * gameWidth;
				float gameY = cameraY * gameHeight;  // 상하반전 제거
				
				paddle4Target = new Vector2(gameX, gameY);
				GD.Print($"[GameManager] 패들4 (오른쪽 발) 목표: {paddle4Target}");
			}
			catch (Exception e)
			{
				GD.Print($"[GameManager] 패들4 좌표 변환 오류: {e}");
			}
		}
		
		// 패들 위치 업데이트 (X축과 Y축 모두)
		UpdatePaddlePositions();
	}
	
	private void UpdatePaddlePositions()
	{
		// 패들 1 (왼쪽 손)
		if (paddle1Target != Vector2.Zero)
		{
			float targetX = Mathf.Clamp(paddle1Target.X, 50, gameWidth - 50);
			float targetY = Mathf.Clamp(paddle1Target.Y, 50, gameHeight - 50);
			Vector2 targetPos = new Vector2(targetX, targetY);
			
			PlayerPaddle1.Position = PlayerPaddle1.Position.Lerp(targetPos, 0.1f);
		}
		
		// 패들 2 (오른쪽 손)
		if (paddle2Target != Vector2.Zero)
		{
			float targetX = Mathf.Clamp(paddle2Target.X, 50, gameWidth - 50);
			float targetY = Mathf.Clamp(paddle2Target.Y, 50, gameHeight - 50);
			Vector2 targetPos = new Vector2(targetX, targetY);
			
			PlayerPaddle2.Position = PlayerPaddle2.Position.Lerp(targetPos, 0.1f);
		}
		
		// 패들 3 (왼쪽 발)
		if (paddle3Target != Vector2.Zero)
		{
			float targetX = Mathf.Clamp(paddle3Target.X, 50, gameWidth - 50);
			float targetY = Mathf.Clamp(paddle3Target.Y, 50, gameHeight - 50);
			Vector2 targetPos = new Vector2(targetX, targetY);
			
			PlayerPaddle3.Position = PlayerPaddle3.Position.Lerp(targetPos, 0.1f);
		}
		
		// 패들 4 (오른쪽 발)
		if (paddle4Target != Vector2.Zero)
		{
			float targetX = Mathf.Clamp(paddle4Target.X, 50, gameWidth - 50);
			float targetY = Mathf.Clamp(paddle4Target.Y, 50, gameHeight - 50);
			Vector2 targetPos = new Vector2(targetX, targetY);
			
			PlayerPaddle4.Position = PlayerPaddle4.Position.Lerp(targetPos, 0.1f);
		}
	}

	private void UpdateBall(float delta)
	{
		Ball.Position += ballVelocity * delta;
		
		// 벽 충돌 체크
		if (Ball.Position.Y <= 0 || Ball.Position.Y >= gameHeight)
		{
			ballVelocity.Y = -ballVelocity.Y;
			Ball.Position = new Vector2(Ball.Position.X, Mathf.Clamp(Ball.Position.Y, 0, gameHeight));
		}
	}

	private void UpdateAIPaddle(float delta)
	{
		// AI 패들은 공을 따라가도록 구현
		float targetY = Ball.Position.Y;
		targetY = Mathf.Clamp(targetY, 50, gameHeight - 50);
		
		AIPaddle.Position = new Vector2(AIPaddle.Position.X,
			Mathf.Lerp(AIPaddle.Position.Y, targetY, aiSpeed * delta / 100.0f));
	}

	private void CheckCollisions()
	{
		// 패들과 공의 충돌 체크
		var ballRect = new Rect2(Ball.Position - new Vector2(10, 10), new Vector2(20, 20));
		var playerRect1 = new Rect2(PlayerPaddle1.Position - new Vector2(10, 50), new Vector2(20, 100));
		var playerRect2 = new Rect2(PlayerPaddle2.Position - new Vector2(10, 50), new Vector2(20, 100));
		var playerRect3 = new Rect2(PlayerPaddle3.Position - new Vector2(10, 50), new Vector2(20, 100));
		var playerRect4 = new Rect2(PlayerPaddle4.Position - new Vector2(10, 50), new Vector2(20, 100));
		var aiRect = new Rect2(AIPaddle.Position - new Vector2(10, 50), new Vector2(20, 100));
		
		// 플레이어 패들 충돌 (모든 패들이 공을 튕길 수 있음)
		if (ballRect.Intersects(playerRect1))
		{
			ballVelocity.X = Mathf.Abs(ballVelocity.X);
			ballVelocity.Y += GD.RandRange(-50, 50);
			ballVelocity = ballVelocity.Normalized() * ballSpeed;
		}
		
		if (ballRect.Intersects(playerRect2))
		{
			ballVelocity.X = Mathf.Abs(ballVelocity.X);
			ballVelocity.Y += GD.RandRange(-50, 50);
			ballVelocity = ballVelocity.Normalized() * ballSpeed;
		}
		
		if (ballRect.Intersects(playerRect3))
		{
			ballVelocity.X = Mathf.Abs(ballVelocity.X);
			ballVelocity.Y += GD.RandRange(-50, 50);
			ballVelocity = ballVelocity.Normalized() * ballSpeed;
		}
		
		if (ballRect.Intersects(playerRect4))
		{
			ballVelocity.X = Mathf.Abs(ballVelocity.X);
			ballVelocity.Y += GD.RandRange(-50, 50);
			ballVelocity = ballVelocity.Normalized() * ballSpeed;
		}
		
		// AI 패들 충돌
		if (ballRect.Intersects(aiRect))
		{
			ballVelocity.X = -Mathf.Abs(ballVelocity.X);
			ballVelocity.Y += GD.RandRange(-50, 50);
			ballVelocity = ballVelocity.Normalized() * ballSpeed;
		}
		
		// 점수 체크
		if (Ball.Position.X <= 0)
		{
			aiScore++;
			ResetBall();
			UpdateScoreDisplay();
		}
		else if (Ball.Position.X >= gameWidth)
		{
			playerScore++;
			ResetBall();
			UpdateScoreDisplay();
		}
	}

	private void ResetBall()
	{
		Ball.Position = new Vector2(gameWidth / 2.0f, gameHeight / 2.0f);
		ballVelocity = new Vector2(ballSpeed, 0).Rotated((float)GD.RandRange(-0.785f, 0.785f)); // -Pi/4 to Pi/4 radians
		
		// 점수에 따라 방향 결정
		if (playerScore > aiScore)
		{
			ballVelocity.X = -Mathf.Abs(ballVelocity.X);
		}
		else
		{
			ballVelocity.X = Mathf.Abs(ballVelocity.X);
		}
	}

	private void UpdateScoreDisplay()
	{
		ScoreLabel.Text = $"플레이어: {playerScore}  |  AI: {aiScore}";
		EmitSignal(nameof(ScoreUpdated), playerScore, aiScore);
	}

	public void RestartGame()
	{
		playerScore = 0;
		aiScore = 0;
		InitializeGame();
	}

	public override void _Input(InputEvent @event)
	{
		if (@event.IsActionPressed("ui_accept"))
		{
			RestartGame();
		}
		else if (@event.IsActionPressed("ui_cancel"))
		{
			gameActive = false;
			EmitSignal(nameof(GameEnded));
		}
	}

	private void UpdateDebugStatus()
	{
		string status = "";
		status += $"서버 연결: {(serverConnected ? "O" : "X")}\n";
		status += $"플레이어 수: {playerCount}\n";
		status += $"손 데이터 개수: {playerHands.Count}\n";
		status += $"발 데이터 개수: {playerFeet.Count}\n";
		
		if (playerHands.Count > 0)
		{
			var firstHand = playerHands[0];
			if (firstHand.ContainsKey("x") && firstHand.ContainsKey("y"))
			{
				float x = 0.0f, y = 0.0f, visibility = 0.0f;
				
				try
				{
					x = firstHand["x"].AsSingle();
					y = firstHand["y"].AsSingle();
					
					if (firstHand.ContainsKey("visibility"))
						visibility = firstHand["visibility"].AsSingle();
				}
				catch (Exception e)
				{
					GD.Print($"[GameManager] 디버그 상태 변환 오류: {e}");
				}
				
				status += $"첫 번째 손 좌표: ({x:F2}, {y:F2})\n";
				status += $"손 visibility: {visibility:F3}\n";
			}
		}
		
		status += $"패들1 (왼쪽 손): {PlayerPaddle1.Position}\n";
		status += $"패들2 (오른쪽 손): {PlayerPaddle2.Position}\n";
		status += $"패들3 (왼쪽 발): {PlayerPaddle3.Position}\n";
		status += $"패들4 (오른쪽 발): {PlayerPaddle4.Position}\n";
		double sinceLastPose = Time.GetUnixTimeFromSystem() - lastPoseTime;
		status += $"마지막 포즈 수신: {sinceLastPose:F1}초 전";
		DebugLabel.Text = status;
	}
} 
