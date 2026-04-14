// include/my_robot_hardware_interface/my_robot_hardware.hpp

#pragma once

#include <string>
#include <vector>
#include <memory>

#include "hardware_interface/system_interface.hpp"
#include "hardware_interface/handle.hpp"
#include "hardware_interface/hardware_info.hpp"
#include "hardware_interface/types/hardware_interface_return_values.hpp"
#include "rclcpp/rclcpp.hpp"
#include "rclcpp_lifecycle/state.hpp"

// Serial communication
#include <termios.h>
#include <unistd.h>
#include <fcntl.h>

namespace my_robot_hardware_interface
{

class MyRobotHardware : public hardware_interface::SystemInterface
{
public:
  RCLCPP_SHARED_PTR_DEFINITIONS(MyRobotHardware)

  // Lifecycle callbacks
  hardware_interface::CallbackReturn on_init(
    const hardware_interface::HardwareComponentInterfaceParams & params) override;
    
  hardware_interface::CallbackReturn on_configure(
    const rclcpp_lifecycle::State & previous_state) override;

  hardware_interface::CallbackReturn on_activate(
    const rclcpp_lifecycle::State & previous_state) override;

  hardware_interface::CallbackReturn on_deactivate(
    const rclcpp_lifecycle::State & previous_state) override;

  // State and command interfaces
  std::vector<hardware_interface::StateInterface> export_state_interfaces() override;
  std::vector<hardware_interface::CommandInterface> export_command_interfaces() override;

  // Control loop
  hardware_interface::return_type read(
    const rclcpp::Time & time, const rclcpp::Duration & period) override;

  hardware_interface::return_type write(
    const rclcpp::Time & time, const rclcpp::Duration & period) override;

private:
  // Serial port helpers
  bool openSerial(const std::string & port, int baud);
  void closeSerial();
  bool writeSerial(const std::string & data);
  std::string readLine();

  int serial_fd_ = -1;
  std::string serial_port_;
  int baud_rate_;

  // Joint state (positions and velocities — rad, rad/s)
  double left_wheel_pos_  = 0.0;
  double right_wheel_pos_ = 0.0;
  double left_wheel_vel_  = 0.0;
  double right_wheel_vel_ = 0.0;

  // Joint commands (velocity in rad/s)
  double left_wheel_cmd_  = 0.0;
  double right_wheel_cmd_ = 0.0;

  rclcpp::Logger logger_ = rclcpp::get_logger("MyRobotHardware");
};

}  // namespace my_robot_hardware_interface