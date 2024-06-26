import tkinter, tkinter.font
import socket
import ssl


HSTEP, VSTEP = 13, 18
WIDTH, HEIGHT = 800, 600

def layout(tokens):
    weight = "normal"
    style = "roman"
    display_list = []
    cursor_x, cursor_y = HSTEP, VSTEP
    for tok in tokens:
        if isinstance(tok, Text):
            for word in tok.text.split():
                font = tkinter.font.Font(
                    size=16,
                    weight=weight,
                    slant=style,
                )
                w = font.measure(word)
                display_list.append((cursor_x, cursor_y, word, font))
                cursor_x += w + font.measure(" ")
                if cursor_x + w > WIDTH - HSTEP:
                    cursor_y += font.metrics("linespace") * 1.25
                    cursor_x = HSTEP
        elif tok.tag == "i":
            style = "italic"
        elif tok.tag == "/i":
            style ="roman"
        elif tok.tag == "b":
            weight = "bold"
        elif tok.tag == "/b":
            weight = "normal"
    return display_list

def show(body):
    in_tag = False
    for c in body:
        if c == "<":
            in_tag = True
        elif c == ">":
            in_tag = False
        elif not in_tag:
            print(c, end="")

def load (url):
    body = url.request()
    show(body)
    
def lex(body):
    out = []
    buffer = ""
    in_tag = False
    for c in body:
        if c == "<":
            in_tag = True
            if buffer: out.append(Text(buffer))
            buffer = ""
        elif c == ">":
            in_tag = False
            out.append(Tag(buffer))
            buffer = ""
        else:
            buffer += c
    if not in_tag and buffer:
        out.append(Text(buffer))
    return out


class URL:
    def __init__(self, url):
        self.scheme, url = url.split("://", 1)
        self.host, url = url.split("/", 1)
        self.path = "/" + url
        assert self.scheme in {"http", "https", "file"}
        
        if self.scheme == "file":
            self.read_local_file()
        
        if "/" not in url:
            url = url + "/"

        if self.scheme == "http":
            self.port = 80
        elif self.scheme == "https":
            self.port = 443
        else:
            self.port = 0
            
        if ":" in self.host:
            self.host, port = self.host.split(":", 1)
            self.port = int(port)
        
    def request(self):
        s = socket.socket(
            family=socket.AF_INET,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP,
        )
        if self.scheme == "https":
            ctx = ssl.create_default_context()
            s = ctx.wrap_socket(s, server_hostname=self.host)

        s.connect((self.host, self.port))
        
        request = "GET {} HTTP/1.0\r\n".format(self.path)
        request += "Host: {}\r\n".format(self.host)
        request += "Connection: close\r\n"
        request += "User-Agent: Python\r\n"
        request += "\r\n"
        s.send(request.encode("utf8"))
        
        response = s.makefile("r", encoding="utf8", newline="\r\n")
        
        statusline = response.readline()
        version, status, explanation = statusline.split(" ", 2)
        
        response_headers = {}
        while True:
            line = response.readline()
            if line == "\r\n": break
            header, value = line.split(":", 1)
            response_headers[header.casefold()] = value.strip()
        
        assert "transfer-encoding" not in response_headers
        assert "content-encoding" not in response_headers
        
        content = response.read()
        s.close()
        
        return content
    
    def read_local_file(self):
        with open(self.path, "r") as f:
            return f.read()
    
class Browser:
    def __init__(self):
        self.SCROLL_STEP = 50
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(
            self.window,
            width=WIDTH,
            height=HEIGHT
        )
        self.canvas.pack()
        self.scroll = 0
        self.window.bind("<Down>", self.scrolldown)
        self.window.bind("<Up>", self.scrollup)
        self.window.bind("<Button-4>", self.scrollup)
        self.window.bind("<Button-5>", self.scrolldown)
        
    def load(self, url):
        body = url.request()
        text = lex(body)
        self.display_list = layout(text)
        self.draw()

    def scrollup(self, e):
        self.scroll -= self.SCROLL_STEP
        self.draw()
    
    def scrolldown(self, e):
        self.scroll += self.SCROLL_STEP
        self.draw()

        # self.canvas.create_oval(100, 100, 150, 150)
#                                x1,  y1,  x2,  y2 
    
    def draw(self):
        self.canvas.delete("all")
        for x, y, c, f in self.display_list:
            if y > self.scroll + HEIGHT: continue
            if y + VSTEP < self.scroll: continue
            self.canvas.create_text(x, y - self.scroll, text=c, font=f)


class Text:
    def __init__(self, text):
        self.text = text


class Tag:
    def __init__(self, tag):
        self.tag = tag


class Layout:
    pass


if __name__ == "__main__":
    import sys
    Browser().load(URL(sys.argv[1]))
    tkinter.mainloop()

# if __name__ == "__main__":
#     import sys
#     try:
#         load(URL(sys.argv[1]))
#     except IndexError:
#         load(URL("file:///home/bolshoy/Desktop/test.txt"))
    
