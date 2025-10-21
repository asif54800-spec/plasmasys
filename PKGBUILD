# Maintainer: Muhammad Asif Rauf <asif54800@gmail.com>
pkgname=plasmasys
pkgver=1.0
pkgrel=1
pkgdesc="A simple Python sensor monitor for the KDE Plasma 6 desktop."
arch=('any')
url="https://github.com/asif54800-spec/plasmasys"
license=('MIT')
depends=('python-pyqt6' 'python-psutil')
optdepends=('wireless_tools: for displaying Wi-Fi SSID')

source=("$pkgname-$pkgver.tar.gz::https://github.com/asif54800-spec/plasmasys/archive/refs/tags/v$pkgver.tar.gz")

# This checksum is for the file we proved is correct
sha256sums=('b2505b2bc866605741bcfb944267a644872ce7c8a29b5d4a17b120124c9ce84e')

# This function is the critical fix
prepare() {
    cd "$pkgname-$pkgver"
}

package() {
    # This will now work, because prepare() moved us into the right folder
    install -Dm755 "plasmasys.py" "$pkgdir/usr/bin/$pkgname"
    install -Dm644 "plasmasys.desktop" "$pkgdir/usr/share/applications/plasmasys.desktop"
    install -Dm644 "plasmasys.svg" "$pkgdir/usr/share/icons/hicolor/scalable/apps/plasmasys.svg"
}
