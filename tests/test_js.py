
from py2max import Patcher

js_file = """
var myval=0;

if (jsarguments.length>1)
	myval = jsarguments[1];

function bang()
{
	outlet(0,"myvalue","is",myval);
}

function msg_int(v)
{
	post("received int " + v + "\\n");
	myval = v;
	bang();
}

function msg_float(v)
{
	post("received float " + v + "\\n");
	myval = v;
	bang();
}

function list()
{
	var a = arrayfromargs(arguments);
	post("received list " + a + "\\n");
	myval = a;
	bang();
}

function anything()
{
	var a = arrayfromargs(messagename, arguments);
	post("received message " + a + "\\n");
	myval = a;
	bang();
}
"""

def test_js():
    with open('outputs/my.js', 'w') as f:
        f.write(js_file)
    p = Patcher('outputs/test_js.maxpat')
    bang = p.add_textbox('button')
    js = p.add_textbox('js my.js hello')
    msg = p.add_message()
    p.link(bang, js)
    p.link(js, msg, 1) # to second inlet 1
    p.save()


