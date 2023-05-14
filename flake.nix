{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-22.11";
  };

  outputs = {
    self,
    nixpkgs,
    ...
  }: let
    pkgs = nixpkgs.legacyPackages.x86_64-linux;
    ach = import ./ACH {inherit pkgs;};
  in {
    formatter.x86_64-linux = pkgs.alejandra;

    devShells.x86_64-linux.default = pkgs.mkShell {
      nativeBuildInputs = with pkgs; [
        (python3.withPackages (ps:
          with ps;
          with python3Packages; [
            pandas
            python-dotenv
            pyperclip
            requests
            plotly
            tabulate
            numpy
          ]))

        ach
      ];
    };
  };
}
