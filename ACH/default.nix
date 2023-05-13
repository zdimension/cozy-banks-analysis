{pkgs, ...}: let
  version = "1.48.0";
in
  pkgs.mkYarnPackage {
    pname = "cozy-ACH";
    inherit version;

    src = pkgs.fetchFromGitHub {
      owner = "cozy";
      repo = "ACH";
      rev = "v${version}";
      sha256 = "sha256-WM65fTNvzCnXqvzvA3gNjiF70JmCR3dUwZdELLjebkY=";
    };

    distPhase = ":"; # disable useless $out/tarballs directory

    packageJSON = ./package.json;
    yarnLock = ./yarn.lock;
  }
