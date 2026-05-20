library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library work;
use work.matverse_metrics_pkg.all;

entity omega_gate is
  port (
    psi_m        : in  metric_milli_t;
    theta_m      : in  metric_milli_t;
    cvar_m       : in  metric_milli_t;
    pole_m       : in  metric_milli_t;
    replay_valid : in  std_logic;
    omega_m      : out omega_milli_t;
    decision     : out std_logic_vector(1 downto 0)
  );
end entity omega_gate;

architecture rtl of omega_gate is
begin
  process (psi_m, theta_m, cvar_m, pole_m, replay_valid)
    variable score : omega_milli_t;
  begin
    score := omega_score_milli(psi_m, theta_m, cvar_m, pole_m);
    omega_m <= score;
    decision <= decide_omega(psi_m, theta_m, cvar_m, pole_m, replay_valid);
  end process;
end architecture rtl;
