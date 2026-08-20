/* =====================================================
   ELOC TECHNOLOGY LAB
   MAIN JAVASCRIPT
   RESPONSIVE + CINEMATIC + ACCESSIBLE
===================================================== */

document.addEventListener("DOMContentLoaded", () => {

    /* =================================================
       GLOBAL ELEMENTS
    ================================================= */

    const body = document.body;

    const menuButton =
        document.getElementById("mobile-menu-button");

    const mobileNavigation =
        document.getElementById("mobile-navigation");

    const header =
        document.getElementById("site-header");


    /* =================================================
       MOBILE MENU
    ================================================= */

    const closeMobileMenu = () => {

        if (!menuButton || !mobileNavigation) {
            return;
        }

        mobileNavigation.classList.remove(
            "mobile-navigation-open"
        );

        menuButton.classList.remove(
            "mobile-menu-active"
        );

        menuButton.setAttribute(
            "aria-expanded",
            "false"
        );

        body.classList.remove(
            "mobile-menu-open"
        );
    };


    const openMobileMenu = () => {

        if (!menuButton || !mobileNavigation) {
            return;
        }

        mobileNavigation.classList.add(
            "mobile-navigation-open"
        );

        menuButton.classList.add(
            "mobile-menu-active"
        );

        menuButton.setAttribute(
            "aria-expanded",
            "true"
        );

        body.classList.add(
            "mobile-menu-open"
        );
    };


    if (menuButton && mobileNavigation) {

        /* ---------------------------------------------
           INITIAL ACCESSIBILITY STATE
        --------------------------------------------- */

        menuButton.setAttribute(
            "aria-expanded",
            "false"
        );

        menuButton.setAttribute(
            "aria-controls",
            "mobile-navigation"
        );


        /* ---------------------------------------------
           OPEN / CLOSE
        --------------------------------------------- */

        menuButton.addEventListener(
            "click",
            event => {

                event.preventDefault();
                event.stopPropagation();

                const isOpen =
                    mobileNavigation.classList.contains(
                        "mobile-navigation-open"
                    );

                if (isOpen) {
                    closeMobileMenu();
                } else {
                    openMobileMenu();
                }

            }
        );


        /* ---------------------------------------------
           CLOSE AFTER MENU LINK
        --------------------------------------------- */

        mobileNavigation
            .querySelectorAll("a")
            .forEach(link => {

                link.addEventListener(
                    "click",
                    () => {
                        closeMobileMenu();
                    }
                );

            });


        /* ---------------------------------------------
           CLOSE WHEN CLICKING OUTSIDE
        --------------------------------------------- */

        document.addEventListener(
            "click",
            event => {

                const isOpen =
                    mobileNavigation.classList.contains(
                        "mobile-navigation-open"
                    );

                if (!isOpen) {
                    return;
                }

                const clickedMenu =
                    mobileNavigation.contains(
                        event.target
                    );

                const clickedButton =
                    menuButton.contains(
                        event.target
                    );

                if (
                    !clickedMenu &&
                    !clickedButton
                ) {
                    closeMobileMenu();
                }

            }
        );


        /* ---------------------------------------------
           ESCAPE KEY
        --------------------------------------------- */

        document.addEventListener(
            "keydown",
            event => {

                if (
                    event.key === "Escape" &&
                    mobileNavigation.classList.contains(
                        "mobile-navigation-open"
                    )
                ) {

                    closeMobileMenu();

                    menuButton.focus();

                }

            }
        );


        /* ---------------------------------------------
           CLOSE ON DESKTOP
        --------------------------------------------- */

        let resizeTimer;

        window.addEventListener(
            "resize",
            () => {

                clearTimeout(resizeTimer);

                resizeTimer = setTimeout(() => {

                    if (window.innerWidth > 900) {
                        closeMobileMenu();
                    }

                }, 100);

            },
            {
                passive: true
            }
        );

    }


    /* =================================================
       SMOOTH SCROLL
    ================================================= */

    document
        .querySelectorAll('a[href^="#"]')
        .forEach(link => {

            link.addEventListener(
                "click",
                event => {

                    const targetId =
                        link.getAttribute("href");


                    if (
                        !targetId ||
                        targetId === "#"
                    ) {
                        return;
                    }


                    let target = null;

                    try {

                        target =
                            document.querySelector(
                                targetId
                            );

                    } catch (error) {

                        return;

                    }


                    if (!target) {
                        return;
                    }


                    event.preventDefault();


                    const headerOffset =
                        header
                            ? header.offsetHeight + 20
                            : 20;


                    const targetPosition =
                        target.getBoundingClientRect().top +
                        window.scrollY -
                        headerOffset;


                    window.scrollTo({
                        top: Math.max(
                            0,
                            targetPosition
                        ),
                        behavior: "smooth"
                    });


                    /*
                       Update browser URL without
                       forcing an unwanted page jump.
                    */

                    if (
                        history.replaceState
                    ) {

                        history.replaceState(
                            null,
                            "",
                            targetId
                        );

                    }

                }
            );

        });


    /* =================================================
       TECHNOLOGY CARD REVEAL
    ================================================= */

    const technologyCards =
        document.querySelectorAll(
            ".technology-card"
        );


    if (technologyCards.length) {

        if (
            "IntersectionObserver" in window
        ) {

            const technologyObserver =
                new IntersectionObserver(
                    entries => {

                        entries.forEach(
                            entry => {

                                if (
                                    !entry.isIntersecting
                                ) {
                                    return;
                                }


                                entry.target.classList.add(
                                    "technology-card-visible"
                                );


                                technologyObserver.unobserve(
                                    entry.target
                                );

                            }
                        );

                    },
                    {
                        threshold: 0.12,
                        rootMargin:
                            "0px 0px -40px 0px"
                    }
                );


            technologyCards.forEach(
                (card, index) => {

                    card.style.setProperty(
                        "--card-delay",
                        `${index * 0.08}s`
                    );

                    technologyObserver.observe(
                        card
                    );

                }
            );

        } else {

            technologyCards.forEach(
                card => {

                    card.classList.add(
                        "technology-card-visible"
                    );

                }
            );

        }

    }


    /* =================================================
       TECHNOLOGY CARD MOUSE LIGHT
    ================================================= */

    const supportsHover =
        window.matchMedia(
            "(hover: hover) and (pointer: fine)"
        ).matches;


    if (
        supportsHover &&
        technologyCards.length
    ) {

        technologyCards.forEach(card => {

            card.addEventListener(
                "pointermove",
                event => {

                    const rect =
                        card.getBoundingClientRect();


                    const x =
                        event.clientX -
                        rect.left;


                    const y =
                        event.clientY -
                        rect.top;


                    card.style.setProperty(
                        "--mouse-x",
                        `${x}px`
                    );

                    card.style.setProperty(
                        "--mouse-y",
                        `${y}px`
                    );

                }
            );


            card.addEventListener(
                "pointerleave",
                () => {

                    card.style.removeProperty(
                        "--mouse-x"
                    );

                    card.style.removeProperty(
                        "--mouse-y"
                    );

                }
            );

        });

    }


    /* =================================================
       GENERAL CINEMATIC REVEAL
    ================================================= */

    const revealElements =
        document.querySelectorAll(
            ".reveal-hidden"
        );


    if (revealElements.length) {

        if (
            "IntersectionObserver" in window
        ) {

            const revealObserver =
                new IntersectionObserver(
                    entries => {

                        entries.forEach(
                            entry => {

                                if (
                                    !entry.isIntersecting
                                ) {
                                    return;
                                }


                                entry.target.classList.add(
                                    "reveal-visible"
                                );


                                revealObserver.unobserve(
                                    entry.target
                                );

                            }
                        );

                    },
                    {
                        threshold: 0.12,
                        rootMargin:
                            "0px 0px -30px 0px"
                    }
                );


            revealElements.forEach(
                element => {

                    revealObserver.observe(
                        element
                    );

                }
            );

        } else {

            revealElements.forEach(
                element => {

                    element.classList.add(
                        "reveal-visible"
                    );

                }
            );

        }

    }


    /* =================================================
       CINEMATIC 3D CARD MOTION
    ================================================= */

    const motionCards =
        document.querySelectorAll(
            ".project-card, " +
            ".featured-project-card, " +
            ".identity-card, " +
            ".engineering-card"
        );


    if (
        supportsHover &&
        motionCards.length
    ) {

        motionCards.forEach(card => {

            card.addEventListener(
                "pointermove",
                event => {

                    const rect =
                        card.getBoundingClientRect();


                    const x =
                        event.clientX -
                        rect.left;


                    const y =
                        event.clientY -
                        rect.top;


                    const centerX =
                        rect.width / 2;


                    const centerY =
                        rect.height / 2;


                    const rotateY =
                        ((x - centerX) /
                            centerX) * 4;


                    const rotateX =
                        ((centerY - y) /
                            centerY) * 4;


                    card.style.setProperty(
                        "--rotate-x",
                        `${rotateX}deg`
                    );

                    card.style.setProperty(
                        "--rotate-y",
                        `${rotateY}deg`
                    );


                    card.style.setProperty(
                        "--mouse-x",
                        `${x}px`
                    );

                    card.style.setProperty(
                        "--mouse-y",
                        `${y}px`
                    );

                }
            );


            card.addEventListener(
                "pointerleave",
                () => {

                    card.style.setProperty(
                        "--rotate-x",
                        "0deg"
                    );

                    card.style.setProperty(
                        "--rotate-y",
                        "0deg"
                    );

                    card.style.removeProperty(
                        "--mouse-x"
                    );

                    card.style.removeProperty(
                        "--mouse-y"
                    );

                }
            );

        });

    }


    /* =================================================
       HEADER SCROLL EFFECT
    ================================================= */

    if (header) {

        let ticking = false;


        const updateHeader = () => {

            if (
                window.scrollY > 40
            ) {

                header.classList.add(
                    "header-scrolled"
                );

            } else {

                header.classList.remove(
                    "header-scrolled"
                );

            }

            ticking = false;

        };


        window.addEventListener(
            "scroll",
            () => {

                if (!ticking) {

                    window.requestAnimationFrame(
                        updateHeader
                    );

                    ticking = true;

                }

            },
            {
                passive: true
            }
        );


        updateHeader();

    }


    /* =================================================
       ACTIVE NAVIGATION
    ================================================= */

    const sections =
        document.querySelectorAll(
            "section[id]"
        );


    const navLinks =
        document.querySelectorAll(
            ".desktop-navigation a[href^='#']"
        );


    if (
        sections.length &&
        navLinks.length &&
        "IntersectionObserver" in window
    ) {

        const sectionObserver =
            new IntersectionObserver(
                entries => {

                    /*
                       Find the section closest to the
                       top of the viewport instead of
                       relying only on callback order.
                    */

                    let activeSection = null;

                    let closestDistance =
                        Infinity;


                    sections.forEach(
                        section => {

                            const rect =
                                section.getBoundingClientRect();


                            const distance =
                                Math.abs(
                                    rect.top -
                                    window.innerHeight *
                                    0.30
                                );


                            if (
                                rect.top <=
                                    window.innerHeight *
                                    0.70 &&
                                rect.bottom >=
                                    window.innerHeight *
                                    0.10 &&
                                distance <
                                    closestDistance
                            ) {

                                closestDistance =
                                    distance;

                                activeSection =
                                    section;

                            }

                        }
                    );


                    if (!activeSection) {
                        return;
                    }


                    const sectionId =
                        activeSection.id;


                    navLinks.forEach(
                        link => {

                            const matches =
                                link.getAttribute(
                                    "href"
                                ) ===
                                `#${sectionId}`;


                            link.classList.toggle(
                                "active",
                                matches
                            );

                        }
                    );

                },
                {
                    threshold: [
                        0.1,
                        0.25,
                        0.5,
                        0.75
                    ],
                    rootMargin:
                        "-10% 0px -25% 0px"
                }
            );


        sections.forEach(
            section => {

                sectionObserver.observe(
                    section
                );

            }
        );

    }


    /* =================================================
       CURRENT PAGE NAVIGATION
       HIGHLIGHT HOME WHEN AT TOP
    ================================================= */

    if (navLinks.length) {

        const updateTopNavigation = () => {

            if (
                window.scrollY <= 80
            ) {

                navLinks.forEach(
                    link => {

                        const href =
                            link.getAttribute(
                                "href"
                            );


                        link.classList.toggle(
                            "active",
                            href === "#home"
                        );

                    }
                );

            }

        };


        window.addEventListener(
            "scroll",
            updateTopNavigation,
            {
                passive: true
            }
        );


        updateTopNavigation();

    }


    /* =================================================
       KEYBOARD ACCESSIBILITY
    ================================================= */

    if (menuButton) {

        menuButton.addEventListener(
            "keydown",
            event => {

                if (
                    event.key === "Enter" ||
                    event.key === " "
                ) {

                    event.preventDefault();

                    menuButton.click();

                }

            }
        );

    }


    /* =================================================
       REDUCED MOTION SUPPORT
    ================================================= */

    const reducedMotion =
        window.matchMedia(
            "(prefers-reduced-motion: reduce)"
        );


    const applyReducedMotion =
        () => {

            if (!reducedMotion.matches) {
                return;
            }


            document
                .querySelectorAll(
                    ".technology-card, " +
                    ".reveal-hidden"
                )
                .forEach(element => {

                    element.classList.add(
                        "technology-card-visible"
                    );

                    element.classList.add(
                        "reveal-visible"
                    );

                });

        };


    applyReducedMotion();


    if (
        typeof reducedMotion.addEventListener ===
        "function"
    ) {

        reducedMotion.addEventListener(
            "change",
            applyReducedMotion
        );

    }


    /* =================================================
       INITIAL PAGE STATE
    ================================================= */

    document.documentElement.classList.add(
        "js-enabled"
    );

});

/* =========================================================
   PROJECT GALLERY
   ========================================================= */

document.addEventListener("DOMContentLoaded", function () {

    const gallery = document.getElementById("project-gallery");
    const preview = document.getElementById("gallery-preview-image");
    const current = document.getElementById("gallery-current");

    if (!gallery || !preview || !current) {
        return;
    }

    const items = gallery.querySelectorAll(".gallery-item");

    items.forEach(function (item) {

        item.addEventListener("click", function () {

            items.forEach(function (galleryItem) {
                galleryItem.classList.remove("active");
            });

            item.classList.add("active");

            preview.src = item.dataset.image;

            current.textContent =
                String(item.dataset.index).padStart(2, "0");

            item.scrollIntoView({
                behavior: "smooth",
                block: "nearest",
                inline: "center"
            });

        });

    });

});