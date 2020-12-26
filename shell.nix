{ pkgs ? import <nixpkgs> { }
}:
let
  argonone = pkgs.callPackage ./default.nix { };
in
pkgs.mkShell {
  buildInputs = [
    argonone
    (pkgs.python3.withPackages (ps: [
      ps.black
      ps.pytest
    ]))
  ];
}
