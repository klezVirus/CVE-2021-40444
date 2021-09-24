function calc(){
    var x = new ActiveXObject("WScript.shell");
    x.Run("cmd /c calc");
}

calc();