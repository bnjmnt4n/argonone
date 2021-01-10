{ sources ? import ./nix/sources.nix { }
, pkgs ? import sources.nixpkgs { }
}:

with pkgs;
let
  # TODO: change
  customPackages = pkgs.callPackage ../nixos-configuration/pkgs { };
  inherit (customPackages.python3Packages) gpiozero smbus2;
in
python3Packages.buildPythonApplication {
  pname = "argonone-rpi4";
  version = lib.fileContents ./version.txt;
  format = "pyproject";

  src = lib.cleanSource ./.;

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
