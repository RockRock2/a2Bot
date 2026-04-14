// ============================================================
// robot_firmware_ros2control.ino
// Updated for ros2_control — receives rad/s, sends rad/s feedback
// ============================================================

// --- Pin Definitions (Cytron MDD3A dual PWM) ---
#define LEFT_AIN1   5
#define LEFT_AIN2   6
#define RIGHT_BIN1  9
#define RIGHT_BIN2  10

#define LEFT_ENC_A  2   // Interrupt
#define LEFT_ENC_B  8
#define RIGHT_ENC_A 3   // Interrupt
#define RIGHT_ENC_B 11

// --- Robot Parameters (UPDATE THESE) ---
const float WHEEL_RADIUS    = 0.033;
const int   TICKS_PER_REV   = 360;
const float MAX_MOTOR_RAD_S = 5.0;    // ← lower this to match your actual motor
                                       //   measure: spin motor at full PWM,
                                       //   count rad/s from encoder feedback
const int   MAX_PWM         = 120;    // ← too fast at 200
const int   PWM_DEADBAND    = 30;
// --- Encoder State ---
volatile long leftTicks  = 0;
volatile long rightTicks = 0;

// --- Velocity tracking ---
long prevLeftTicks  = 0;
long prevRightTicks = 0;
unsigned long prevTime = 0;
float leftVelRad  = 0.0;
float rightVelRad = 0.0;

// --- Serial ---
String inputBuffer = "";
const int SEND_INTERVAL_MS = 20;   // 50Hz feedback
unsigned long lastSendTime = 0;

// ============================================================
void leftEncoderISR() {
  leftTicks += (digitalRead(LEFT_ENC_B) == HIGH) ? 1 : -1;
}

void rightEncoderISR() {
  rightTicks += (digitalRead(RIGHT_ENC_B) == HIGH) ? -1 : 1;
}

// ============================================================
// Convert rad/s to PWM for MDD3A dual-PWM mode
// ============================================================
void setMotorRadS(int pin1, int pin2, float radS) {
  int dir = (radS >= 0) ? 1 : 0;
  float ratio = abs(radS) / MAX_MOTOR_RAD_S;
  int pwm = (int)(ratio * MAX_PWM);

  if (pwm > 0 && pwm < PWM_DEADBAND) pwm = PWM_DEADBAND;
  pwm = constrain(pwm, 0, MAX_PWM);

  if (pwm == 0) {
    analogWrite(pin1, 0);
    analogWrite(pin2, 0);
  } else if (dir == 1) {
    analogWrite(pin1, pwm);
    analogWrite(pin2, 0);
  } else {
    analogWrite(pin1, 0);
    analogWrite(pin2, pwm);
  }
}

void stopMotors() {
  analogWrite(LEFT_AIN1, 0); analogWrite(LEFT_AIN2, 0);
  analogWrite(RIGHT_BIN1, 0); analogWrite(RIGHT_BIN2, 0);
}

// ============================================================
// Parse "V<left_rad_s>,<right_rad_s>\n"
// Example: "V1.047,-1.047\n"
// ============================================================
void parseVelocityCommand(String cmd) {
  cmd.trim();
  if (!cmd.startsWith("V")) return;
  int comma = cmd.indexOf(',');
  if (comma < 0) return;

  float leftRad  = cmd.substring(1, comma).toFloat();
  float rightRad = cmd.substring(comma + 1).toFloat();

  setMotorRadS(LEFT_AIN1,  LEFT_AIN2,  leftRad);
  setMotorRadS(RIGHT_BIN1, RIGHT_BIN2, rightRad);
}

// ============================================================
void setup() {
  Serial.begin(115200);

  pinMode(LEFT_AIN1,  OUTPUT); pinMode(LEFT_AIN2,  OUTPUT);
  pinMode(RIGHT_BIN1, OUTPUT); pinMode(RIGHT_BIN2, OUTPUT);
  stopMotors();

  pinMode(LEFT_ENC_A,  INPUT_PULLUP); pinMode(LEFT_ENC_B,  INPUT_PULLUP);
  pinMode(RIGHT_ENC_A, INPUT_PULLUP); pinMode(RIGHT_ENC_B, INPUT_PULLUP);

  attachInterrupt(digitalPinToInterrupt(LEFT_ENC_A),  leftEncoderISR,  RISING);
  attachInterrupt(digitalPinToInterrupt(RIGHT_ENC_A), rightEncoderISR, RISING);

  prevTime = millis();
}

// ============================================================
void loop() {
  // Read serial commands
  while (Serial.available() > 0) {
    char c = (char)Serial.read();
    if (c == '\n') {
      parseVelocityCommand(inputBuffer);
      inputBuffer = "";
    } else {
      inputBuffer += c;
    }
  }

  unsigned long now = millis();

  // Compute and send velocity feedback at 50Hz
  if (now - lastSendTime >= SEND_INTERVAL_MS) {
    noInterrupts();
    long lTicks = leftTicks;
    long rTicks = rightTicks;
    interrupts();

    float dt = (now - prevTime) / 1000.0;
    if (dt > 0) {
      float radPerTick = (2.0 * PI) / TICKS_PER_REV;
      leftVelRad  = ((lTicks - prevLeftTicks)  * radPerTick) / dt;
      rightVelRad = ((rTicks - prevRightTicks) * radPerTick) / dt;
    }

    // Send: "F<left_pos_rad>,<right_pos_rad>,<left_vel>,<right_vel>\n"
    float leftPosRad  = lTicks * (2.0 * PI / TICKS_PER_REV);
    float rightPosRad = rTicks * (2.0 * PI / TICKS_PER_REV);

    Serial.print("F");
    Serial.print(leftPosRad,  4);
    Serial.print(",");
    Serial.print(rightPosRad, 4);
    Serial.print(",");
    Serial.print(leftVelRad,  4);
    Serial.print(",");
    Serial.println(rightVelRad, 4);

    prevLeftTicks  = lTicks;
    prevRightTicks = rTicks;
    prevTime       = now;
    lastSendTime   = now;
  }
}
