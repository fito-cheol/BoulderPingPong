using Godot;
using System;
using System.Runtime.CompilerServices;
using Godot.Collections;

public partial class Signals : Node
{  
	//chat signals
	public static Action<Dictionary> onPoseDataReceived = delegate { }; 
	public static Signals instance;
	public override void _EnterTree()
	{ 
		instance = this;
		//debug with time
		GD.Print("Signals entered tree at " + Time.GetTicksMsec());
		GD.Print("Signals instance: " + instance);
	}  
	
}
