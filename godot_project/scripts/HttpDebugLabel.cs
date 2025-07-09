using Godot;
using System;
using System.Text;


public partial class HttpDebugLabel : Node
{  
	[Export]
	RichTextLabel debugLabel1;
	[Export]
	RichTextLabel debugLabel2;

	[Export]
	Button RequestButton;

	HttpRequest httpRequest;
	HttpRequest httpRequest2;

	public override void _Ready()
	{
		RequestButton.Pressed += OnRequestButtonPressed;
		httpRequest = GetNode<HttpRequest>("HTTPRequest");
		httpRequest.RequestCompleted += OnRequestCompleted;
		httpRequest2 = GetNode<HttpRequest>("HTTPRequest2");
		httpRequest2.RequestCompleted += OnRequestCompleted2; 
	}

	private void OnRequestButtonPressed()
	{
		httpRequest.Request("https://api.github.com/repos/godotengine/godot/releases/latest"); 
		httpRequest2.Request("https://api.github.com/repos/godotengine/godot/releases/latest"); 
	}

	private void OnRequestCompleted(long result, long responseCode, string[] headers, byte[] body)
	{
		Godot.Collections.Dictionary json = Json.ParseString(Encoding.UTF8.GetString(body)).AsGodotDictionary();
		GD.Print(json["name"]);
		debugLabel1.Text = json["name"].ToString();
	}

	private void OnRequestCompleted2(long result, long responseCode, string[] headers, byte[] body)
	{
		Json json = new Json();
		var parseResult = json.Parse(body.GetStringFromUtf8());
		if (parseResult != Error.Ok)
		{
			GD.Print("JSON 파싱 실패: ", parseResult);
			return;
		}
		var jsonData = json.Data; 
		GD.Print(jsonData.AsGodotDictionary()["name"]);
		debugLabel2.Text = jsonData.AsGodotDictionary()["name"].ToString();
	}

	
}
