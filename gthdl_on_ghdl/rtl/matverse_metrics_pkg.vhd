library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

package matverse_metrics_pkg is
  subtype metric_milli_t is natural range 0 to 1000;
  subtype omega_milli_t is natural range 0 to 1000;

  constant PSI_MIN_MILLI   : metric_milli_t := 850;
  constant CVAR_MAX_MILLI  : metric_milli_t := 50;
  constant OMEGA_MIN_MILLI : omega_milli_t  := 850;

  constant DECISION_BLOCK  : std_logic_vector(1 downto 0) := "00";
  constant DECISION_REVIEW : std_logic_vector(1 downto 0) := "01";
  constant DECISION_HOLD   : std_logic_vector(1 downto 0) := "10";
  constant DECISION_PASS   : std_logic_vector(1 downto 0) := "11";

  function omega_score_milli(
    psi_m   : metric_milli_t;
    theta_m : metric_milli_t;
    cvar_m  : metric_milli_t;
    pole_m  : metric_milli_t
  ) return omega_milli_t;

  function decide_omega(
    psi_m        : metric_milli_t;
    theta_m      : metric_milli_t;
    cvar_m       : metric_milli_t;
    pole_m       : metric_milli_t;
    replay_valid : std_logic
  ) return std_logic_vector;
end package matverse_metrics_pkg;

package body matverse_metrics_pkg is
  function omega_score_milli(
    psi_m   : metric_milli_t;
    theta_m : metric_milli_t;
    cvar_m  : metric_milli_t;
    pole_m  : metric_milli_t
  ) return omega_milli_t is
    variable weighted_sum : natural;
    variable score        : natural;
  begin
    weighted_sum :=
      (400 * psi_m) +
      (300 * theta_m) +
      (200 * (1000 - cvar_m)) +
      (100 * pole_m);

    score := (weighted_sum + 500) / 1000;

    if score > 1000 then
      return 1000;
    else
      return score;
    end if;
  end function;

  function decide_omega(
    psi_m        : metric_milli_t;
    theta_m      : metric_milli_t;
    cvar_m       : metric_milli_t;
    pole_m       : metric_milli_t;
    replay_valid : std_logic
  ) return std_logic_vector is
    variable omega_m : omega_milli_t;
  begin
    omega_m := omega_score_milli(psi_m, theta_m, cvar_m, pole_m);

    if replay_valid /= '1' then
      return DECISION_BLOCK;
    elsif (psi_m >= PSI_MIN_MILLI) and
          (cvar_m <= CVAR_MAX_MILLI) and
          (omega_m >= OMEGA_MIN_MILLI) then
      return DECISION_PASS;
    elsif omega_m >= 500 then
      return DECISION_REVIEW;
    else
      return DECISION_BLOCK;
    end if;
  end function;
end package body matverse_metrics_pkg;
