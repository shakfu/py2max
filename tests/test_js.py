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
    with open("outputs/my.js", "w") as f:
        f.write(js_file)
    p = Patcher("outputs/test_js.maxpat")
    bang = p.add_textbox("button")
    js = p.add_textbox("js my.js hello")
    msg = p.add_message()
    l1 = p.link(bang, js)
    l2 = p.link(js, msg, 1)  # to second inlet 1
    p.save()

    assert bang.maxclass == "button"
    assert js.maxclass == "newobj"
    assert js.text == "js my.js hello"
    assert msg.maxclass == "message"

    assert len(p._lines) == 2
    assert l1.source[0] == bang.id
    assert l1.destination[0] == js.id
    assert l2.source[0] == js.id
    assert l2.destination[0] == msg.id
    assert l2.destination[1] == 1  # second inlet
