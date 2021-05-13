from Xlib.display import Display
from Xlib import X, threaded
from Xlib.ext import record
from Xlib.protocol import rq
import time
import threading

debug_key_event = False
debug_key_press = False
debug_new_listener = False

local_dpy = Display()
record_dpy = Display()

# Check if the extension is present
if not record_dpy.has_extension('RECORD'):
    print('KeyListener Error: RECORD extension not found')
    sys.exit(1)
r = record_dpy.record_get_version(0, 0)
print(f'KeyListener: RECORD extension version {r.major_version}.{r.minor_version}')

keysym_map = {
    32: 'SPACE',
    39: '\'',
    44: ',',
    45: '-',
    46: '.',
    47: '/',
    48: '0',
    49: '1',
    50: '2',
    51: '3',
    52: '4',
    53: '5',
    54: '6',
    55: '7',
    56: '8',
    57: '9',
    59: ';',
    61: '=',
    91: '[',
    92: '\\',
    93: ']',
    96: '`',
    97: 'a',
    98: 'b',
    99: 'c',
    100: 'd',
    101: 'e',
    102: 'f',
    103: 'g',
    104: 'h',
    105: 'i',
    106: 'j',
    107: 'k',
    108: 'l',
    109: 'm',
    110: 'n',
    111: 'o',
    112: 'p',
    113: 'q',
    114: 'r',
    115: 's',
    116: 't',
    117: 'u',
    118: 'v',
    119: 'w',
    120: 'x',
    121: 'y',
    122: 'z',
    65293: 'ENTER',
    65307: 'ESC',
    65360: 'HOME',
    65361: 'ARROW_LEFT',
    65362: 'ARROW_UP',
    65363: 'ARROW_RIGHT',
    65505: 'L_SHIFT',
    65506: 'R_SHIFT',
    65507: 'L_CTRL',
    65508: 'R_CTRL',
    65513: 'L_ALT',
    65514: 'R_ALT',
    65515: 'SUPER_KEY',
    65288: 'BACKSPACE',
    65364: 'ARROW_DOWN',
    65365: 'PAGE_UP',
    65366: 'PAGE_DOWN',
    65367: 'END',
    65377: 'PRTSCRN',
    65535: 'DELETE',
    65383: 'PRINT?',
    65509: 'CAPS_LOCK',
    65289: 'TAB',
    65470: 'F1',
    65471: 'F2',
    65472: 'F3',
    65473: 'F4',
    65474: 'F5',
    65475: 'F6',
    65476: 'F7',
    65477: 'F8',
    65478: 'F9',
    65479: 'F10',
    65480: 'F11',
    65481: 'F12'

}


class KeyListener(object):
    def __init__(self):
        '''
        Really simple implementation of a global hotkey creator
        Simply define your hotkeys by creating a KeyListener object,
        call add_key_listener(combination, listener) to create your
        hotkey and then run start_listener() to start listeneing
        for key presses/releases.
        Key combinations are separated by plus signs.
        ex:
        >>> my_keylistener = KeyListener()
        >>> my_keylistener.add_key_listener('L_CTRL+L_SHIFT+s', lambda: print('Ctrl+Shift+S Pressed'))
        >>> my_keylistener.start_listener()
        '''
        self.pressed = set()
        self.listeners = {}

    def keysym_to_character(self, sym):
        if sym in keysym_map:
            return keysym_map[sym]
        else:
            return sym

    def event_handler(self, reply):
        '''
        Called when a Xlib event is fired
        '''
        data = reply.data
        while len(data):
            event, data = rq.EventField(None).parse_binary_value(
                data, record_dpy.display, None, None)

            keycode = event.detail
            keysym = local_dpy.keycode_to_keysym(event.detail, 0)

            if keysym in keysym_map:
                character = self.keysym_to_character(keysym)
                if debug_key_event:
                    print(character)
                if event.type == X.KeyPress:
                    self.press(character)
                elif event.type == X.KeyRelease:
                    self.release(character)

    def setup_listener(self):
        # Monitor keypress and button press
        self.ctx = record_dpy.record_create_context(
            0,
            [record.AllClients],
            [{
                'core_requests': (0, 0),
                'core_replies': (0, 0),
                'ext_requests': (0, 0, 0, 0),
                'ext_replies': (0, 0, 0, 0),
                'delivered_events': (0, 0),
                'device_events': (X.KeyReleaseMask, X.ButtonReleaseMask),
                'errors': (0, 0),
                'client_started': False,
                'client_died': False,
            }])

        record_dpy.record_enable_context(self.ctx, self.event_handler)
        record_dpy.record_free_context(self.ctx)

    def start_listener(self):
        self.setup_listener()
    
    def stop_listener(self):
        local_dpy.record_disable_context(self.ctx)
        local_dpy.flush()

    def get_callback(self, character):

        # return self.listeners.get(tuple(self.pressed), False)

        my_callback = None

        for index, (key, listener) in enumerate(self.listeners.items()):
            listener_keys_in_pressed = all(key in self.pressed for key in key)
            if listener_keys_in_pressed:
                my_callback = listener

        return my_callback

    def press(self, character):
        '''
        Called on a key press
        '''
        self.pressed.add(character)

        # callback = self.listeners.get(tuple(self.pressed), False)

        callback = self.get_callback(character)

        if debug_key_press:
            print('Keypress, currently pressed:', tuple(self.pressed))
        if callback and callable(callback):
            callback()

    def release(self, character):
        '''
        Called on a key release event
        '''
        if character in self.pressed:
            self.pressed.remove(character)

    def add_key_listener(self, combination, listener):
        '''
        Adds a listener for a hotkey
        '''
        keys = tuple(combination.split('+'))
        if debug_new_listener:
            print('Added new key listener for:', str(keys))
        self.listeners[keys] = listener


class ThreadedKeyListener(KeyListener):
    def __init__(self):
        '''
        Threaded/asynchronous version of the KeyListener class
        '''
        self.pressed = set()
        self.listeners = {}
        self.thread = None

    def start_listener(self):
        if self.thread:
            return

        print('setup listener')
        self.thread = threading.Thread(
            target=self.setup_listener, name='Keyboard Listener Thread')
        self.thread.do_run = True
        self.thread.start()
        print('after setup listener')


if __name__ == '__main__':
    my_listener = KeyListener()

    def my_key_listener_fn():
        print('!!!! Ran my_key_listener_fn')
    
    def close_listener_fn():
        my_listener.stop_listener()

    my_listener.add_key_listener('L_ALT+L_SHIFT+a', my_key_listener_fn)
    my_listener.add_key_listener('ESC', close_listener_fn)

    my_listener.start_listener()
