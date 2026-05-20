library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library work;
use work.matverse_metrics_pkg.all;

entity replay_checker is
  port (
    current_psi_m      : in  metric_milli_t;
    current_theta_m    : in  metric_milli_t;
    current_cvar_m     : in  metric_milli_t;
    current_pole_m     : in  metric_milli_t;
    expected_psi_m     : in  metric_milli_t;
    expected_theta_m   : in  metric_milli_t;
    expected_cvar_m    : in  metric_milli_t;
    expected_pole_m    : in  metric_milli_t;
    current_decision   : in  std_logic_vector(1 downto 0);
    expected_decision  : in  std_logic_vector(1 downto 0);
    replay_valid       : out std_logic
  );
end entity replay_checker;

architecture rtl of replay_checker is
begin
  process (
    current_psi_m,
    current_theta_m,
    current_cvar_m,
    current_pole_m,
    expected_psi_m,
    expected_theta_m,
    expected_cvar_m,
    expected_pole_m,
    current_decision,
    expected_decision
  )
  begin
    if (current_psi_m = expected_psi_m) and
       (current_theta_m = expected_theta_m) and
       (current_cvar_m = expected_cvar_m) and
       (current_pole_m = expected_pole_m) and
       (current_decision = expected_decision) then
      replay_valid <= '1';
    else
      replay_valid <= '0';
    end if;
  end process;
end architecture rtl;
