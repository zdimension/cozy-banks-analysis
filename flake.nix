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
      nativeBuildInputs = with pkgs; let
        pandasql = pkgs.python3Packages.buildPythonPackage rec {
          pname = "pandasql";
          version = "0.7.3";

          src = pkgs.python3Packages.fetchPypi {
            inherit version;
            inherit pname;
            sha256 = "sha256-HrJIhpCGQ1p9hSgevZ/lJdadnZVKDc64VPcajQ/Y3mk=";
          };

          buildInputs = with python3Packages; [sqlalchemy pandas];
          doCheck = false;
        };
        currency-converter = pkgs.python3Packages.buildPythonPackage rec {
          pname = "currency-converter";
          version = "0.17.9";

          src = pkgs.python3Packages.fetchPypi {
            inherit version;
            pname = "CurrencyConverter";
            sha256 = "sha256-P4mu0VJRgc9XHSSwJ85opWd1d8UaJunKpqyL60MwJpY=";
          };

          buildInputs = with python3Packages; [setuptools-scm];

          doCheck = false;
        };
      in [
        (python3.withPackages (ps:
          with ps;
          with python3Packages; [
            pandas
            pandasql
            python-dotenv
            pygments
            pyperclip
            requests
            plotly
            tabulate
            numpy
            pre-commit-hooks
            sqlalchemy
            prompt-toolkit
            currency-converter
            yapf
          ]))

        ach
        pre-commit
      ];
    };
  };
}
