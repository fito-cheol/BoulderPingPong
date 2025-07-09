using Godot;
using System;
using Godot.Collections;
using System.Collections.Generic; 

public partial class PoseDataReceiver : Node
{ 
    public Action<Dictionary> PoseDataReceived;
 
    [Export]
    public Label DebugJsonLabel;
    [Export]
    public Label DebugWSStatusLabel;
    
    private WebSocketPeer webSocket;
    private string wsUrl = "ws://localhost:8080";
    private Dictionary currentPoseData = new Dictionary();
    private bool isConnected = false;
    private double requestStartTime = 0.0;

    public override void _Ready()
    { 
        webSocket = new WebSocketPeer();
        
        GD.Print("[PoseDataReceiver] 초기화 완료");
        GD.Print("[PoseDataReceiver] WebSocket URL: ", wsUrl);
        
        // WebSocket 연결 시작
        ConnectWebSocket();
    }
    
    public override void _Process(double delta)
    {
        // WebSocket 상태 확인 및 메시지 처리
        webSocket.Poll();
        
        var state = webSocket.GetReadyState();
        if (state == WebSocketPeer.State.Open)
        {
            if (!isConnected)
            {
                isConnected = true;
                DebugWSStatusLabel.Text = "연결 완료";
            }
            
            // 메시지 수신
            while (webSocket.GetAvailablePacketCount() > 0)
            {
                var packet = webSocket.GetPacket();
                var message = packet.GetStringFromUtf8();
                GD.Print($"[PoseDataReceiver] WebSocket 메시지 수신: {message.Length} 문자");
                ProcessWebSocketMessage(message);
            }
        }
        else if (state == WebSocketPeer.State.Closed)
        {
            if (isConnected)
            {
                isConnected = false;
                DebugWSStatusLabel.Text = "연결 끊김";
                // 재연결 시도
                ConnectWebSocket();
            }
        }
        else if (state == WebSocketPeer.State.Connecting)
        {
            DebugWSStatusLabel.Text = "연결 중...";
        }
        else if (state == WebSocketPeer.State.Closing)
        { 
            DebugWSStatusLabel.Text = "연결 종료 중...";
        }
    }
    
    private void ConnectWebSocket()
    {
        GD.Print("[PoseDataReceiver] WebSocket 연결 시도 중...");
        var error = webSocket.ConnectToUrl(wsUrl);
        if (error != Error.Ok)
        {
            GD.Print("[PoseDataReceiver] WebSocket 연결 실패: ", error);
        }
        else
        {
            GD.Print("[PoseDataReceiver] WebSocket 연결 요청 전송됨");
        }
    }
    
    private void ProcessWebSocketMessage(string message)
    {
        try
        {
            GD.Print($"[PoseDataReceiver] 원본 메시지 길이: {message.Length}");
            GD.Print($"[PoseDataReceiver] 원본 메시지 (처음 200자): {message.Substring(0, Math.Min(200, message.Length))}");
            
            // JSON 파싱
            Json json = new Json();
            var parseResult = json.Parse(message);
            if (parseResult != Error.Ok)    
            {
                GD.Print("[PoseDataReceiver] JSON 파싱 실패: ", parseResult);
                GD.Print("[PoseDataReceiver] 실패한 메시지: ", message);
                return;
            }
            
            var poseData = json.Data;
            GD.Print($"[PoseDataReceiver] JSON 파싱 성공, 데이터 타입: {poseData.VariantType}");
            
            if (poseData.VariantType == Variant.Type.Dictionary)
            {   
                currentPoseData = poseData.AsGodotDictionary();
                isConnected = true;
                
                // 디버깅: 데이터 구조 확인
                GD.Print($"[PoseDataReceiver] 현재 포즈 데이터 키들: {string.Join(", ", currentPoseData.Keys)}");
                
                if (currentPoseData.ContainsKey("players"))
                {
                    var playersVariant = currentPoseData["players"];
                    GD.Print($"[PoseDataReceiver] players 타입: {playersVariant.VariantType}");
                    
                    if (playersVariant.VariantType == Variant.Type.Array)
                    {
                        var players = playersVariant.AsGodotArray();
                        GD.Print($"[PoseDataReceiver] 플레이어 배열 크기: {players.Count}");
                        
                        if (players.Count > 0)
                        {
                            var firstPlayer = players[0];
                            GD.Print($"[PoseDataReceiver] 첫 번째 플레이어 타입: {firstPlayer.VariantType}");
                            
                            if (firstPlayer.VariantType == Variant.Type.Dictionary)
                            {
                                var playerDict = firstPlayer.AsGodotDictionary();
                                GD.Print($"[PoseDataReceiver] 플레이어 키들: {string.Join(", ", playerDict.Keys)}");
                                
                                if (playerDict.ContainsKey("hands"))
                                {
                                    var handsVariant = playerDict["hands"];
                                    GD.Print($"[PoseDataReceiver] hands 타입: {handsVariant.VariantType}");
                                    
                                    if (handsVariant.VariantType == Variant.Type.Array)
                                    {
                                        var hands = handsVariant.AsGodotArray();
                                        GD.Print($"[PoseDataReceiver] 손 데이터 개수: {hands.Count}");
                                    }
                                }
                            }
                        }
                    }
                }
                
                if (DebugJsonLabel != null)
                {
                    string jsonStr = Json.Stringify(poseData);
                    if (jsonStr.Length > 1000)
                        jsonStr = jsonStr.Substring(0, 1000) + "\n... (생략)";
                    DebugJsonLabel.Text = jsonStr;
                }
                
                GD.Print("[PoseDataReceiver] Signals.onPoseDataReceived 호출");
                
                // Dictionary를 직접 전달
                try
                {
                    var poseDict = poseData.AsGodotDictionary();
                    if (poseDict != null)
                    {
                        Signals.onPoseDataReceived(poseDict);
                        GD.Print("[PoseDataReceiver] 데이터 전달 성공");
                    }
                    else
                    {
                        GD.Print("[PoseDataReceiver] poseData를 Dictionary로 변환할 수 없습니다.");
                    }
                }
                catch (Exception e)
                {
                    GD.Print($"[PoseDataReceiver] Signals.onPoseDataReceived 호출 중 오류: {e}");
                }
            }
            else
            {
                GD.Print("[PoseDataReceiver] 잘못된 포즈 데이터 형식");
                GD.Print($"[PoseDataReceiver] 예상: Dictionary, 실제: {poseData.VariantType}");
            }
        }
        catch (Exception e)
        {
            GD.Print("[PoseDataReceiver] WebSocket 메시지 처리 오류: ", e);
            GD.Print("[PoseDataReceiver] 오류 발생한 메시지: ", message);
        }
    }

    public Dictionary GetCurrentPoseData()
    {
        return currentPoseData;
    }

    public bool IsServerConnected()
    {
        return isConnected && webSocket.GetReadyState() == WebSocketPeer.State.Open;
    }

    public int GetPlayerCount()
    {
        if (currentPoseData.ContainsKey("players"))
        {
            var playersVariant = currentPoseData["players"];
            if (playersVariant.VariantType == Variant.Type.Array)
            {
                var players = playersVariant.AsGodotArray();
                return players.Count;
            }
        }
        return 0;
    }

    public Godot.Collections.Array GetPlayerHands(int playerIndex)
    {
        if (playerIndex < GetPlayerCount())
        {
            var playersVariant = currentPoseData["players"];
            if (playersVariant.VariantType == Variant.Type.Array)
            {
                var players = playersVariant.AsGodotArray();
                if (playerIndex < players.Count)
                {
                    var playerVariant = players[playerIndex];
                    if (playerVariant.VariantType == Variant.Type.Dictionary)
                    {
                        var player = playerVariant.AsGodotDictionary();
                        if (player.ContainsKey("hands"))
                        {
                            var handsVariant = player["hands"];
                            if (handsVariant.VariantType == Variant.Type.Array)
                            {
                                return handsVariant.AsGodotArray();
                            }
                        }
                    }
                }
            }
        }
        return new Godot.Collections.Array();
    }

    public Godot.Collections.Array GetPlayerFeet(int playerIndex)
    {
        if (playerIndex < GetPlayerCount())
        {
            var playersVariant = currentPoseData["players"];
            if (playersVariant.VariantType == Variant.Type.Array)
            {
                var players = playersVariant.AsGodotArray();
                if (playerIndex < players.Count)
                {
                    var playerVariant = players[playerIndex];
                    if (playerVariant.VariantType == Variant.Type.Dictionary)
                    {
                        var player = playerVariant.AsGodotDictionary();
                        if (player.ContainsKey("feet"))
                        {
                            var feetVariant = player["feet"];
                            if (feetVariant.VariantType == Variant.Type.Array)
                            {
                                return feetVariant.AsGodotArray();
                            }
                        }
                    }
                }
            }
        }
        return new Godot.Collections.Array();
    }

    public Dictionary GetPlayerHead(int playerIndex)
    {
        if (playerIndex < GetPlayerCount())
        {
            var playersVariant = currentPoseData["players"];
            if (playersVariant.VariantType == Variant.Type.Array)
            {
                var players = playersVariant.AsGodotArray();
                if (playerIndex < players.Count)
                {
                    var playerVariant = players[playerIndex];
                    if (playerVariant.VariantType == Variant.Type.Dictionary)
                    {
                        var player = playerVariant.AsGodotDictionary();
                        if (player.ContainsKey("head"))
                        {
                            var headVariant = player["head"];
                            if (headVariant.VariantType == Variant.Type.Dictionary)
                            {
                                return headVariant.AsGodotDictionary();
                            }
                        }
                    }
                }
            }
        }
        return new Dictionary();
    }

    public Dictionary GetPlayerBody(int playerIndex)
    {
        if (playerIndex < GetPlayerCount())
        {
            var playersVariant = currentPoseData["players"];
            if (playersVariant.VariantType == Variant.Type.Array)
            {
                var players = playersVariant.AsGodotArray();
                if (playerIndex < players.Count)
                {
                    var playerVariant = players[playerIndex];
                    if (playerVariant.VariantType == Variant.Type.Dictionary)
                    {
                        var player = playerVariant.AsGodotDictionary();
                        if (player.ContainsKey("body"))
                        {
                            var bodyVariant = player["body"];
                            if (bodyVariant.VariantType == Variant.Type.Dictionary)
                            {
                                return bodyVariant.AsGodotDictionary();
                            }
                        }
                    }
                }
            }
        }
        return new Dictionary();
    }
} 