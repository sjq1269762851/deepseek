# 仓库说明
存储AI全栈过程中的作业和个人实践


# 作业
## 第四章五子棋作业
1、在单次调用python脚本生成的基础上做了两点优化：
   * 可以支持多次对话
   * 支持在浏览器上对话，但是输出格式还需要优化下

2、使用说明
```
1>、python3 main.py
2>、浏览器访问http://localhost:5000/
3>、对话日志保存在conversation.log内
```


## 第五章RAG作业
1、作业沒有使用pyjupter的方式（原因：1、本地环境有点问题； 2、pyjupter没办法把代码模块化），而是直接在后台跑python，通过浏览器对话的形式来处理
   * 支持多轮对话

2、使用说明
```
1>、python3 main.py
2>、浏览器访问http://localhost:5000/
3>、对话日志保存在conversation.log内
``` 