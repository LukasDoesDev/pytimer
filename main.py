import datetime
import decimal
import timeit
import config
from key_listener import ThreadedKeyListener
from gi.repository import Gtk, Gdk, Pango
import gi
gi.require_version('Gtk', '3.0')


# key listener setup
pytimer_key_listener = ThreadedKeyListener()

# global variables
app_on = True
timer_on = False
timer_label = None
timer_label_after_decimal = None
list_of_splits = None
start = None
timer_paused_at = None

# 7200s = 2h
# 1800s = 30min
# = 9000s = 2h 30min


def seconds_to_string(seconds):

    native_str = str(datetime.timedelta(seconds=seconds))

    split_by_decimal_point = native_str.split('.')

    try:
        # remove zeroes in end of decimal string
        while split_by_decimal_point[1].endswith('0'):
            split_by_decimal_point[1] = split_by_decimal_point[1][:-1]
    except IndexError:
        pass

    try:
        # remove zeroes in the start of the string
        while split_by_decimal_point[0].startswith('0:'):
            split_by_decimal_point[0] = split_by_decimal_point[0][2:]
    except IndexError:
        pass

    try:
        # remove zeroes in the start of the string
        while split_by_decimal_point[0].startswith('00:'):
            split_by_decimal_point[0] = split_by_decimal_point[0][3:]
    except IndexError:
        pass

    output = '.'.join(split_by_decimal_point)

    return output


# todo UI code

timer_font = Pango.FontDescription('monospace heavy')


class Window(Gtk.Window):
    def __init__(self):
        global timer_label
        global timer_label_after_decimal
        global list_of_splits

        Gtk.Window.__init__(self, title='PyTimer')
        self.set_border_width(10)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(vbox)

        title_label = Gtk.Label()
        title_label.set_markup(f'{config.game} {config.category}')
        title_label.set_name('title-label')  # sets the id in the CSS
        vbox.pack_start(title_label, True, True, 0)

        list_of_splits = Gtk.Box(spacing=6)
        vbox.pack_start(list_of_splits, True, True, 0)

        timer_label = Gtk.Label()
        timer_label.set_markup('00')
        timer_label.set_name('timer-label-left')  # sets the id in the CSS

        timer_label_after_decimal = Gtk.Label()
        timer_label_after_decimal.set_markup('.00')
        timer_label_after_decimal.set_name(
            'timer-label-right')  # sets the id in the CSS

        # timer_toggle = Gtk.Box()
        timer_toggle_wrapper = Gtk.EventBox()
        timer_toggle_wrapper.connect(
            'button-press-event', self.timer_toggle_handler)
        vbox.pack_start(timer_toggle_wrapper, True, True, 0)

        self.timer_toggle = Gtk.Box()
        self.timer_toggle.props.halign = Gtk.Align.CENTER
        self.timer_toggle.set_name('timer-label-btn')  # sets the id in the CSS
        timer_toggle_wrapper.add(self.timer_toggle)

        self.timer_toggle.add(timer_label)
        self.timer_toggle.add(timer_label_after_decimal)

    def update_timer(self):
        timer_full_str = seconds_to_string(duration)

        timer_str_split = timer_full_str.split('.')

        timer_str_before_decimal = timer_str_split[0]
        timer_str_after_decimal = timer_str_split[1]

        # limit decimal stuff to 2 chars
        timer_str_after_decimal = timer_str_after_decimal[:2]

        timer_label.set_markup(timer_str_before_decimal)
        timer_label_after_decimal.set_markup('.' + timer_str_after_decimal)
        pass

    def timer_toggle_handler(self, widget, event):
        print('timer_toggle_handler', self.timer_toggle, event)

        if event.button == config.mouse_controls['start_pause_resume_timer']:
            # default: left click
            self.start_pause_resume_timer()
        elif event.button == config.mouse_controls['reset_timer']:
            # default: right click
            self.reset_timer()

    def start_pause_resume_timer(self):
        print('start_pause_resume_timer')
        global timer_on
        global timer_paused_at
        global start
        style_ctx = self.timer_toggle.get_style_context()
        if timer_on:
            # PAUSE
            timer_paused_at = timeit.default_timer()
            timer_on = False
            style_ctx.remove_class('timer_on')
        else:
            if start is None:
                # FIRST LAUNCH/AFTER RESET
                start = timeit.default_timer()
            else:
                # RESUME
                start += timeit.default_timer() - timer_paused_at
            timer_on = True
            style_ctx.add_class('timer_on')

    def reset_timer(self):
        print('reset_timer')
        global timer_on
        global timer_paused_at
        global start
        style_ctx = self.timer_toggle.get_style_context()

        timer_label.set_markup('00')
        timer_label_after_decimal.set_markup('.00')

        timer_paused_at = timeit.default_timer()
        timer_on = False
        start = None
        style_ctx.remove_class('timer_on')

    def exit(self, widget):
        exit_pytimer()


def exit_pytimer():
    global app_on
    print('exiting pytimer')
    app_on = False
    print('set pytimer window state to off')
    pytimer_key_listener.stop_listener()
    print('stopped pytimer hotkey listener')
    print('exited pytimer')


# start hotkey listener
print('start hotkey listener')
pytimer_key_listener.start_listener()


# todo setup window
print('setup window')
cssProvider = Gtk.CssProvider()
cssProvider.load_from_path('styles.css')
screen = Gdk.Screen.get_default()
styleContext = Gtk.StyleContext()
styleContext.add_provider_for_screen(
    screen, cssProvider, Gtk.STYLE_PROVIDER_PRIORITY_USER)

win = Window()
win.set_events(Gdk.EventMask.BUTTON_PRESS_MASK)
win.connect('destroy', win.exit)
win.show_all()


# todo add keybinds here
def set_window_size():
    win.resize(200, 300)


pytimer_key_listener.add_key_listener(
    config.hotkeys['set_window_size'], set_window_size)
pytimer_key_listener.add_key_listener(config.hotkeys['exit'], exit_pytimer)
pytimer_key_listener.add_key_listener(
    config.hotkeys['start_pause_resume_timer'], win.start_pause_resume_timer)
pytimer_key_listener.add_key_listener(
    config.hotkeys['reset_timer'], win.reset_timer)

set_window_size()


# todo main loop

while app_on:

    if timer_on and start is not None:
        duration = timeit.default_timer() - start
        win.update_timer()

    Gtk.main_iteration()
