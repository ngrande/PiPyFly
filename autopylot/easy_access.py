import urwid
import autopylot.control


quadcopter = autopylot.control.Quadcopter()
YAW_STEP = 5
TILT_STEP = 5
THROTTLE_STEP = 1

def handle_user_input(key):
	""" handles the user input """
	user_input.set_text("Input: {!s}".format(repr(key)))

	if key == 'I':  # only with SHIFT
		quadcopter.turn_on()
	elif key == 'O':  # only with SHIFT
		quadcopter.turn_off()
	elif key == ' ':
		quadcopter.hover()
	elif key in ['up', 'w']:
		quadcopter.change_tilt(quadcopter.TiltSide.front, TILT_STEP)
	elif key in ['down', 's']:
		quadcopter.change_tilt(quadcopter.TiltSide.front, -TILT_STEP)
	elif key in ['left', 'a']:
		quadcopter.change_tilt(quadcopter.TiltSide.left, TILT_STEP)
	elif key in ['right', 'd']:
		quadcopter.change_tilt(quadcopter.TiltSide.left, -TILT_STEP)
	elif key == 'q':
		quadcopter.change_yaw(-YAW_STEP)
	elif key == 'e':
		quadcopter.change_yaw(YAW_STEP)
	elif key == '+':
		quadcopter.change_overall_throttle(quadcopter.request_total_throttle() / 4 + THROTTLE_STEP)
	elif key =='-':
		quadcopter.change_overall_throttle(quadcopter.request_total_throttle() / 4 - THROTTLE_STEP)

	# update status fields
	update_states()


def update_states():
	""" updates the throttle display """
	if not quadcopter.turned_on:
		drone_state.set_text(('off', u"OFF"))
		motor_fl_throttle.set_text(('throttle', u"NA"))
		motor_fr_throttle.set_text(('throttle', u"NA"))
		motor_rl_throttle.set_text(('throttle', u"NA"))
		motor_rr_throttle.set_text(('throttle', u"NA"))
		total_throttle.set_text(('throttle', u"NA"))
	else:
		drone_state.set_text(('on', u"ON"))
		motor_fl_throttle.set_text(('throttle', u"{!s}".format(quadcopter.request_throttle(quadcopter.MotorSide.front_left))))
		motor_fr_throttle.set_text(('throttle', u"{!s}".format(quadcopter.request_throttle(quadcopter.MotorSide.front_right))))
		motor_rl_throttle.set_text(('throttle', u"{!s}".format(quadcopter.request_throttle(quadcopter.MotorSide.rear_left))))
		motor_rr_throttle.set_text(('throttle', u"{!s}".format(quadcopter.request_throttle(quadcopter.MotorSide.rear_right))))
		total_throttle.set_text(('throttle', u"{!s}".format(quadcopter.request_total_throttle())))
		


palette = [
		('legend', '', '', '', 'white', '#a06'),
		('throttle', 'black', 'yellow'),
		('background', 'white', 'black'),
		('input', 'black', 'white'),
		('on', '', '', '', 'black', '#0d0'),
		('off', '', '', '', 'white', '#d00'),
]

motor_fl_throttle = urwid.Text(('throttle', u"FL"), align='center')
motor_fr_throttle = urwid.Text(('throttle', u"FR"), align='center')
motor_rl_throttle = urwid.Text(('throttle', u"RL"), align='center')
motor_rr_throttle = urwid.Text(('throttle', u"RR"), align='center')
total_throttle = urwid.Text(('throttle', u"NA"), align='center')
user_input = urwid.Text(('input', u""), align='center')
drone_state = urwid.Text(('throttle', u"OFF"), align='center')
name = urwid.Text(u"Easy Access", align='center')
legend = urwid.Text(('legend', U"I: ignite | O: off | SPACE: hover | w: front | a: left | s: rear | d: right | q: ccw | e: cw | +: up | -: down"), align='center')

placeholder = urwid.SolidFill()

loop = urwid.MainLoop(placeholder, palette, unhandled_input=handle_user_input)
loop.screen.set_terminal_properties(colors=256)
loop.widget = urwid.AttrMap(placeholder, 'background')
loop.widget.original_widget = urwid.Filler(urwid.Pile([]))

div = urwid.Divider(u'-')
inv_div = urwid.Divider()

pile = loop.widget.base_widget

motor_grid_top = urwid.GridFlow([], 10, 1, 1, 'center')
motor_grid_bottom = urwid.GridFlow([], 10, 1, 1, 'center')
for motor in [motor_fl_throttle, motor_fr_throttle]:
	motor_grid_top.contents.append((motor, motor_grid_top.options()))
for motor in [motor_rl_throttle, motor_rr_throttle]:
	motor_grid_bottom.contents.append((motor, motor_grid_bottom.options()))

for item in [name, div, legend, div, user_input, drone_state, 
			div, motor_grid_top, total_throttle, motor_grid_bottom]:
	pile.contents.append((item, pile.options()))

try:
	loop.run()
finally:
	quadcopter.turn_off()



# vim: tabstop=4 shiftwidth=4 noexpandtab
