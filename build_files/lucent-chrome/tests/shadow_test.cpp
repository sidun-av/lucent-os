// The shadow image the KWindowShadow tiles are cut from.
#include "shadow.h"
#include <QtTest>

class ShadowTest : public QObject
{
    Q_OBJECT
private Q_SLOTS:
    void paddingMatchesDecoration()
    {
        // gen_aurorae.padding() for --shadow-window light (without the 1 px ring):
        // reach = 1.1 * 110 - 20 = 101; top = 101 - 50 = 51; bottom = 151.
        const QMargins p = LucentShadow::padding(LucentShadow::windowDrops(false, true));
        QCOMPARE(p.left(), 101);
        QCOMPARE(p.right(), 101);
        QCOMPARE(p.top(), 51);
        QCOMPARE(p.bottom(), 151);
    }
    void windowAreaIsCutOut()
    {
        const auto drops = LucentShadow::windowDrops(false, true);
        const QMargins p = LucentShadow::padding(drops);
        const int half = LucentShadow::coreHalf(drops, 18);
        QCOMPARE(half, 18 + 141);    // 1.1 * 110 + 20
        const int core = 2 * half + 1;
        const QImage img = LucentShadow::render(drops, 18, p);
        QCOMPARE(img.width(), p.left() + core + p.right());
        QCOMPARE(img.height(), p.top() + core + p.bottom());
        // the centre pixel and the rounded rectangle are transparent ...
        QCOMPARE(qAlpha(img.pixel(p.left() + half, p.top() + half)), 0);
        QCOMPARE(qAlpha(img.pixel(p.left() + 2, p.top() + half)), 0);
        // ... outside the window's rounded corner the shadow shows, as on the decoration
        QVERIFY(qAlpha(img.pixel(p.left(), p.top())) > 0);
        // a real shadow along the straight edges (the -20 spread layer survives)
        const int below = qAlpha(img.pixel(p.left() + half, p.top() + core + 8));
        const int above = qAlpha(img.pixel(p.left() + half, p.top() - 8));
        const int side = qAlpha(img.pixel(p.left() - 8, p.top() + half));
        QVERIFY2(below > 40, qPrintable(QString::number(below)));
        QVERIFY(below > side);
        QVERIFY(side > above);
    }
    void inactiveIsLighter()
    {
        const auto a = LucentShadow::windowDrops(true, true);
        const auto i = LucentShadow::windowDrops(true, false);
        QCOMPARE(a.size(), i.size());
        for (int k = 0; k < a.size(); ++k)
            QVERIFY(i[k].color.alpha() < a[k].color.alpha());
    }
};

QTEST_GUILESS_MAIN(ShadowTest)
#include "shadow_test.moc"
