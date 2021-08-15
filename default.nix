{ sources ? import ./nix/sources.nix { }
, pkgs ? import sources.nixpkgs { }
}:

with pkgs;
let
  colorzero = pkgs.python3Packages.callPackage ./colorzero.nix { };
  rpi-gpio = pkgs.python3Packages.callPackage ./rpi-gpio.nix { };
  pigpio = pkgs.callPackage ./pigpio.nix { };
  pigpio-py = pkgs.python3Packages.callPackage ./pigpio-py.nix { pigpio-c = pigpio; };
  gpiozero = pkgs.python3Packages.callPackage ./gpiozero.nix {
    inherit colorzero rpi-gpio pigpio-py;
    # withPigpio = false;
    # withRpiGpio = true;
  };
  smbus2 = pkgs.python3Packages.callPackage ./smbus2.nix { };
in
  python3Packages.buildPythonApplication {
    pname = "argonone-rpi4";
    version = lib.fileContents ./version.txt;
    format = "pyproject";

  src = pkgs.nix-gitignore.gitignoreSource [ ] ./.;

  propagatedBuildInputs = [
    # Python inputs
    python3Packages.click
    gpiozero
    smbus2
    python3Packages.toml

    # Other required programs/libraries
    pkgs.libraspberrypi
  ];

  doSetuptoolsCheck = false;
  installCheckPhase = ''
    $out/bin/argononed.py --help
    $out/bin/argononed_poweroff.py --help
  '';

  meta = with lib; {
    description = "Argon One Service and Control Scripts for Raspberry Pi 4";
    homepage = "https://github.com/drewrisinger/argonone";
    license = licenses.gpl3Plus;
    maintainers = with maintainers; [ drewrisinger ];
  };
}
