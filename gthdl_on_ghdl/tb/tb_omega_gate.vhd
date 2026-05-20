library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library work;
use work.matverse_metrics_pkg.all;

entity tb_omega_gate is
end entity tb_omega_gate;

architecture sim of tb_omega_gate is
  signal psi_m        : metric_milli_t := 0;
  signal theta_m      : metric_milli_t := 0;
  signal cvar_m       : metric_milli_t := 0;
  signal pole_m       : metric_milli_t := 0;
  signal replay_valid : std_logic := '0';
  signal omega_m      : omega_milli_t;
  signal decision     : std_logic_vector(1 downto 0);

  signal replay_check_valid : std_logic;
begin
  dut : entity work.omega_gate
    port map (
      psi_m        => psi_m,
      theta_m      => theta_m,
      cvar_m       => cvar_m,
      pole_m       => pole_m,
      replay_valid => replay_valid,
      omega_m      => omega_m,
      decision     => decision
    );

  replay_check : entity work.replay_checker
    port map (
      current_psi_m     => psi_m,
      current_theta_m   => theta_m,
      current_cvar_m    => cvar_m,
      current_pole_m    => pole_m,
      expected_psi_m    => 885,
      expected_theta_m  => 790,
      expected_cvar_m   => 45,
      expected_pole_m   => 1000,
      current_decision  => decision,
      expected_decision => DECISION_PASS,
      replay_valid      => replay_check_valid
    );

  stimulus : process
  begin
    report "Scenario 1: Cassandra substrato PASS vector";
    psi_m <= 885;
    theta_m <= 790;
    cvar_m <= 45;
    pole_m <= 1000;
    replay_valid <= '1';
    wait for 10 ns;

    assert omega_m = 882
      report "Expected omega_m=882 for substrato vector"
      severity error;

    assert decision = DECISION_PASS
      report "Expected PASS for substrato vector"
      severity error;

    assert replay_check_valid = '1'
      report "Expected deterministic replay check to pass"
      severity error;

    report "Scenario 2: high CVaR must prevent PASS even with high omega";
    psi_m <= 857;
    theta_m <= 770;
    cvar_m <= 73;
    pole_m <= 1000;
    replay_valid <= '1';
    wait for 10 ns;

    assert omega_m = 859
      report "Expected omega_m=859 for high CVaR vector"
      severity error;

    assert decision /= DECISION_PASS
      report "High CVaR vector must not PASS"
      severity error;

    report "Scenario 3: replay invalid must BLOCK";
    psi_m <= 885;
    theta_m <= 790;
    cvar_m <= 45;
    pole_m <= 1000;
    replay_valid <= '0';
    wait for 10 ns;

    assert decision = DECISION_BLOCK
      report "Replay invalid vector must BLOCK"
      severity error;

    report "Scenario 4: low coherence must not PASS";
    psi_m <= 500;
    theta_m <= 250;
    cvar_m <= 1000;
    pole_m <= 0;
    replay_valid <= '1';
    wait for 10 ns;

    assert decision /= DECISION_PASS
      report "Low coherence vector must not PASS"
      severity error;

    report "GTHDL-on-GHDL simulation PASS";
    wait;
  end process;
end architecture sim;
