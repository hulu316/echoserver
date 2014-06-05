仿tornado实现的一个EchoServer，因为完全没有复杂的业务逻辑，用ab测试，可以达到8K+qps。
玩法：运行app，然后在浏览器输入http://IP:8000/?say=something，回车，页面就会显示something。