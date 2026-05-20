library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity ledger_register is
  generic (
    WIDTH : positive := 256
  );
  port (
    clk              : in  std_logic;
    reset_n          : in  std_logic;
    commit_enable    : in  std_logic;
    receipt_in       : in  std_logic_vector(WIDTH - 1 downto 0);
    previous_hash_in : in  std_logic_vector(WIDTH - 1 downto 0);
    committed        : out std_logic;
    ledger_state_out : out std_logic_vector(WIDTH - 1 downto 0)
  );
end entity ledger_register;

architecture rtl of ledger_register is
  signal ledger_state : std_logic_vector(WIDTH - 1 downto 0) := (others => '0');

  function rotate_left_one(v : std_logic_vector) return std_logic_vector is
    variable r : std_logic_vector(v'range);
  begin
    r := v(v'left - 1 downto v'right) & v(v'left);
    return r;
  end function;
begin
  process (clk, reset_n)
  begin
    if reset_n = '0' then
      ledger_state <= (others => '0');
      committed <= '0';
    elsif rising_edge(clk) then
      if commit_enable = '1' then
        -- Simulation fingerprint only. This is not a cryptographic hash.
        ledger_state <= receipt_in xor rotate_left_one(previous_hash_in);
        committed <= '1';
      else
        committed <= '0';
      end if;
    end if;
  end process;

  ledger_state_out <= ledger_state;
end architecture rtl;
