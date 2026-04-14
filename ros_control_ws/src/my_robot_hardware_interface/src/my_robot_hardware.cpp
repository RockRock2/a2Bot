// src/my_robot_hardware.cpp

#include "my_robot_hardware_interface/my_robot_hardware.hpp"
#include "pluginlib/class_list_macros.hpp"

#include <chrono>
#include <cstring>
#include <sstream>
#include <thread>

#include <iomanip>    // ← add this
#include <unistd.h>   // ← add this

namespace my_robot_hardware_interface
{

// ============================================================
// on_init — called when URDF is loaded
// Reads parameters from URDF <ros2_control> tag
// ============================================================
hardware_interface::CallbackReturn MyRobotHardware::on_init(
  const hardware_interface::HardwareComponentInterfaceParams & params)
{
  if (hardware_interface::SystemInterface::on_init(params) !=
      hardware_interface::CallbackReturn::SUCCESS) {
    return hardware_interface::CallbackReturn::ERROR;
  }

  // Read parameters from URDF hardware tag
  serial_port_ = info_.hardware_parameters.count("serial_port") ?
    info_.hardware_parameters.at("serial_port") : "/dev/arduino";
  baud_rate_   = info_.hardware_parameters.count("baud_rate") ?
    std::stoi(info_.hardware_parameters.at("baud_rate")) : 115200;

  RCLCPP_INFO(logger_, "Initialising MyRobotHardware on %s at %d baud",
    serial_port_.c_str(), baud_rate_);

  // Validate joints — must have exactly 2 joints
  if (info_.joints.size() != 2) {
    RCLCPP_ERROR(logger_, "Expected 2 joints, got %zu", info_.joints.size());
    return hardware_interface::CallbackReturn::ERROR;
  }

  return hardware_interface::CallbackReturn::SUCCESS;
}

// ============================================================
// on_configure — open serial port
// ============================================================
hardware_interface::CallbackReturn MyRobotHardware::on_configure(
  const rclcpp_lifecycle::State &)
{
  RCLCPP_INFO(logger_, "Configuring — opening serial port %s", serial_port_.c_str());

  if (!openSerial(serial_port_, baud_rate_)) {
    RCLCPP_ERROR(logger_, "Failed to open serial port %s", serial_port_.c_str());
    return hardware_interface::CallbackReturn::ERROR;
  }

  // Flush Arduino bootloader garbage
  std::this_thread::sleep_for(std::chrono::milliseconds(2000));
  tcflush(serial_fd_, TCIFLUSH);

  RCLCPP_INFO(logger_, "Serial port opened successfully");
  return hardware_interface::CallbackReturn::SUCCESS;
}

// ============================================================
// on_activate — start control loop
// ============================================================
hardware_interface::CallbackReturn MyRobotHardware::on_activate(
  const rclcpp_lifecycle::State &)
{
  RCLCPP_INFO(logger_, "Activating MyRobotHardware");

  // Reset state
  left_wheel_pos_  = 0.0;
  right_wheel_pos_ = 0.0;
  left_wheel_vel_  = 0.0;
  right_wheel_vel_ = 0.0;
  left_wheel_cmd_  = 0.0;
  right_wheel_cmd_ = 0.0;

  return hardware_interface::CallbackReturn::SUCCESS;
}

// ============================================================
// on_deactivate — stop motors safely
// ============================================================
hardware_interface::CallbackReturn MyRobotHardware::on_deactivate(
  const rclcpp_lifecycle::State &)
{
  RCLCPP_INFO(logger_, "Deactivating — stopping motors");
  writeSerial("V0.0000,0.0000\n");
  return hardware_interface::CallbackReturn::SUCCESS;
}

// ============================================================
// export_state_interfaces — what the framework can READ
// ============================================================
std::vector<hardware_interface::StateInterface>
MyRobotHardware::export_state_interfaces()
{
  std::vector<hardware_interface::StateInterface> interfaces;

  interfaces.emplace_back("left_wheel_joint",  "position", &left_wheel_pos_);
  interfaces.emplace_back("left_wheel_joint",  "velocity", &left_wheel_vel_);
  interfaces.emplace_back("right_wheel_joint", "position", &right_wheel_pos_);
  interfaces.emplace_back("right_wheel_joint", "velocity", &right_wheel_vel_);

  return interfaces;
}

// ============================================================
// export_command_interfaces — what the framework can WRITE
// ============================================================
std::vector<hardware_interface::CommandInterface>
MyRobotHardware::export_command_interfaces()
{
  std::vector<hardware_interface::CommandInterface> interfaces;

  interfaces.emplace_back("left_wheel_joint",  "velocity", &left_wheel_cmd_);
  interfaces.emplace_back("right_wheel_joint", "velocity", &right_wheel_cmd_);

  return interfaces;
}

// ============================================================
// read() — called every control loop cycle
// Read encoder data from Arduino
// ============================================================
hardware_interface::return_type MyRobotHardware::read(
  const rclcpp::Time &, const rclcpp::Duration &)
{
  std::string line = readLine();
  if (line.empty() || line[0] != 'F') {
    return hardware_interface::return_type::OK;  // not ready yet
  }

  // Parse "F<l_pos>,<r_pos>,<l_vel>,<r_vel>"
  try {
    line = line.substr(1);  // remove 'F'
    std::stringstream ss(line);
    std::string token;
    std::vector<double> vals;

    while (std::getline(ss, token, ',')) {
      vals.push_back(std::stod(token));
    }

    if (vals.size() == 4) {
      left_wheel_pos_  = vals[0];
      right_wheel_pos_ = vals[1];
      left_wheel_vel_  = vals[2];
      right_wheel_vel_ = vals[3];
    }
  } catch (const std::exception & e) {
    RCLCPP_WARN_THROTTLE(logger_, *rclcpp::Clock::make_shared(),
      1000, "Failed to parse serial data: %s", e.what());
  }

  return hardware_interface::return_type::OK;
}

// ============================================================
// write() — called every control loop cycle
// Send velocity commands to Arduino
// ============================================================
hardware_interface::return_type MyRobotHardware::write(
  const rclcpp::Time &, const rclcpp::Duration &)
{
  // Format: "V<left_rad_s>,<right_rad_s>\n"
  std::ostringstream cmd;
  cmd << "V"
      << std::fixed << std::setprecision(4) << left_wheel_cmd_
      << ","
      << std::fixed << std::setprecision(4) << right_wheel_cmd_
      << "\n";

  writeSerial(cmd.str());
  return hardware_interface::return_type::OK;
}

// ============================================================
// Serial helpers
// ============================================================
bool MyRobotHardware::openSerial(const std::string & port, int baud)
{
  serial_fd_ = open(port.c_str(), O_RDWR | O_NOCTTY | O_NONBLOCK);
  if (serial_fd_ < 0) return false;

  struct termios tty;
  memset(&tty, 0, sizeof tty);
  cfgetispeed(&tty);

  speed_t speed = B115200;
  if (baud == 9600)   speed = B9600;
  if (baud == 57600)  speed = B57600;
  if (baud == 115200) speed = B115200;

  cfsetispeed(&tty, speed);
  cfsetospeed(&tty, speed);

  tty.c_cflag = (tty.c_cflag & ~CSIZE) | CS8;
  tty.c_cflag |= (CLOCAL | CREAD);
  tty.c_cflag &= ~(PARENB | PARODD | CSTOPB | CRTSCTS);
  tty.c_iflag &= ~(IXON | IXOFF | IXANY | IGNBRK | BRKINT | PARMRK | ISTRIP | INLCR | IGNCR | ICRNL);
  tty.c_lflag = 0;
  tty.c_oflag = 0;
  tty.c_cc[VMIN]  = 0;
  tty.c_cc[VTIME] = 1;  // 0.1 second read timeout

  if (tcsetattr(serial_fd_, TCSANOW, &tty) != 0) {
    close(serial_fd_);
    serial_fd_ = -1;
    return false;
  }
  return true;
}

void MyRobotHardware::closeSerial()
{
  if (serial_fd_ >= 0) {
    close(serial_fd_);
    serial_fd_ = -1;
  }
}

bool MyRobotHardware::writeSerial(const std::string & data)
{
  if (serial_fd_ < 0) return false;
  return ::write(serial_fd_, data.c_str(), data.size()) == (ssize_t)data.size();
}

std::string MyRobotHardware::readLine()
{
  if (serial_fd_ < 0) return "";

  std::string line;
  char c;
  while (true) {
    int n = ::read(serial_fd_, &c, 1);
    if (n <= 0) break;
    if (c == '\n') break;
    if (c != '\r') line += c;
  }
  return line;
}

}  // namespace my_robot_hardware_interface

// Register plugin with pluginlib
PLUGINLIB_EXPORT_CLASS(
  my_robot_hardware_interface::MyRobotHardware,
  hardware_interface::SystemInterface)