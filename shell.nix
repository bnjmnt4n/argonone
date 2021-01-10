{ sources ? import ./nix/sources.nix { }
, pkgs ? import sources.nixpkgs { }
}:
let
  argonone = pkgs.callPackage ./default.nix { };
  niv = (import sources.niv { }).niv;
in
pkgs.mkShell {
  buildInputs = [
    argonone
    (pkgs.python3.withPackages (ps: [
      ps.black
      ps.pytest
    ]))
    niv
  ];
}
