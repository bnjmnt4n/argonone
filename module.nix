{ lib, pkgs, config, ... }:

with lib;
let
  cfg = config.services.argonone;
in
{
  options.services.argonone = { };

  config = mkIf cfg.enable {
    systemd.services.argonone = {
      description = "Argon One Fan & Button Service";
      after = [ "multi-user.target" ];
      serviceConfig = {
        ExecStart = "${argonone-rpi4}/bin/argononed.py";
        Type = "simple";
        Restart = "always";
        RemainAfterExit = true;
      };
      restartIfChanged = true;
    };
    systemd.shutdown = {
      argonone-poweroff = "${argonone-rpi4}/bin/argononed-poweroff.py";
    };
  };
}
