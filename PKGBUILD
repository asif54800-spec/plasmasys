

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
sha256sums=('5738fe54dbb9a637e146e6dc1167d3b89e185837205fb0d495548260c7fdfdd7')

prepare() {
    cd "$pkgname-$pkgver"
}

package() {
    install -Dm755 "plasmasys.py" "$pkgdir/usr/bin/$pkgname"
    install -Dm644 "plasmasys.desktop" "$pkgdir/usr/share/applications/plasmasys.desktop"
    install -Dm644 "plasmasys.svg" "$pkgdir/usr/share/icons/hicolor/scalable/apps/plasmasys.svg"
}
