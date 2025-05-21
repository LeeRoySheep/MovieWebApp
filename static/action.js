// Wrap all DOM-dependent code inside a DOMContentLoaded event listener
document.addEventListener('DOMContentLoaded', function() {
    // Get the canvas element and its 2D rendering context
    const canvas = document.getElementById('pixelCanvas');
    const ctx = canvas.getContext('2d');

    // Text content and properties for the canvas-drawn text
    const mainText = "Dynamic Pixelmap Background";
    const subText = "Watch the colors change!";
    const thirdText = "This text has pixel-level contrast!";
    let fontSizeH1 = 48; // px - will be dynamically adjusted
    let fontSizeP = 24; // px - will be dynamically adjusted
    const fontName = "Inter, sans-serif"; // Ensure font is available or fallback

    /**
     * Generates a random hexadecimal color code, biased towards darker shades (slightly brighter than before).
     *
     * @returns {string} A random hexadecimal color code (e.g., '#RRGGBB').
     */
    function generateRandomColor() {
        // Limit random byte generation to a darker range (0-150) - adjusted for brighter background
        const getRandomDarkByte = () => Math.floor(Math.random() * 151); // Max value 150

        const r = getRandomDarkByte();
        const g = getRandomDarkByte();
        const b = getRandomDarkByte();

        // Helper to convert a number to a two-digit hexadecimal string
        const toHex = (c) => {
            const hex = c.toString(16);
            return hex.length === 1 ? '0' + hex : hex; // Ensure two digits (e.g., 'f' becomes '0f')
        };

        // Combine RGB components into a full hexadecimal color string
        return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
    }

    // Function to set up canvas dimensions and handle window resizing
    function resizeCanvas() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;

        // Dynamically adjust font sizes based on screen width for responsiveness
        if (canvas.width < 600) {
            fontSizeH1 = 32; // Smaller font for small screens
            fontSizeP = 18;
        } else if (canvas.width < 900) {
            fontSizeH1 = 40; // Medium font for medium screens
            fontSizeP = 22;
        } else {
            fontSizeH1 = 48; // Original font size for large screens
            fontSizeP = 24;
        }
        // No need to clear here, animate will clear and redraw
    }

    // Define parameters for drawing background pixels
    const pixelSize = 1; // The size (width and height) of each square pixel in pixels (remains 1)
    const pixelsPerFrame = 500; // The number of random background pixels to draw in each animation frame (increased for quicker change)

    /**
     * Draws a single randomly colored pixel on the canvas.
     * The pixel's position is snapped to a grid defined by `pixelSize`.
     */
    function drawRandomBackgroundPixel() {
        const x = Math.floor(Math.random() * (canvas.width / pixelSize)) * pixelSize;
        const y = Math.floor(Math.random() * (canvas.height / pixelSize)) * pixelSize;
        const color = generateRandomColor();
        ctx.fillStyle = color;
        ctx.fillRect(x, y, pixelSize, pixelSize);
    }

    /**
     * Draws text on the canvas with pixel-level contrast to the background.
     * This function uses an off-screen canvas to get the text mask.
     */
    function drawContrastingText() {
        // Create an off-screen canvas for text rendering
        const tempCanvas = document.createElement('canvas');
        const tempCtx = tempCanvas.getContext('2d');
        tempCanvas.width = canvas.width;
        tempCanvas.height = canvas.height;

        // Set text properties for the off-screen canvas
        tempCtx.font = `${fontSizeH1}px ${fontName}`;
        tempCtx.textAlign = 'center';
        tempCtx.textBaseline = 'middle';
        tempCtx.fillStyle = 'black'; // Draw text in black to get a clear mask

        // Calculate text positions (centered)
        const centerX = canvas.width / 2;
        const centerY = canvas.height / 2;
        // Adjust lineHeight based on current fontSizeH1
        const lineHeight = fontSizeH1 * 1.2; // Approximate line height

        // Draw text on the off-screen canvas
        tempCtx.fillText(mainText, centerX, centerY - lineHeight);
        tempCtx.font = `${fontSizeP}px ${fontName}`;
        tempCtx.fillText(subText, centerX, centerY);
        tempCtx.fillText(thirdText, centerX, centerY + lineHeight);

        // Get pixel data from the main canvas (current background)
        const mainImageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const mainPixels = mainImageData.data;

        // Get pixel data from the off-screen text canvas (text mask)
        const tempImageData = tempCtx.getImageData(0, 0, tempCanvas.width, tempCanvas.height);
        const tempPixels = tempImageData.data;

        // Loop through all pixels
        for (let i = 0; i < mainPixels.length; i += 4) {
            // Check if the pixel on the temporary canvas is part of the text (opaque black)
            if (tempPixels[i + 3] > 0) { // If this pixel is part of the text
                // Get the background color at this pixel position from main canvas
                const bgR = mainPixels[i];
                const bgG = mainPixels[i + 1];
                const bgB = mainPixels[i + 2];

                // Calculate the inverse color for contrast.
                mainPixels[i] = 255 - bgR;
                mainPixels[i + 1] = 255 - bgG;
                mainPixels[i + 2] = 255 - bgB;
            }
        }

        // Put the modified pixel data back onto the main canvas
        ctx.putImageData(mainImageData, 0, 0);
    }

    /**
     * The main animation loop.
     * It draws a set number of random background pixels per frame and then redraws the contrasting text.
     */
    function animate() {
        // Draw multiple background pixels in each frame (accumulating effect)
        for (let i = 0; i < pixelsPerFrame; i++) {
            drawRandomBackgroundPixel();
        }

        // Draw the contrasting text on top of the background
        drawContrastingText();

        // Request the next animation frame, creating a smooth loop
        requestAnimationFrame(animate);
    }

    // Initial setup and animation start
    resizeCanvas(); // Set the initial canvas size and font sizes
    animate();      // Start the pixel drawing animation

    // Add an event listener to resize the canvas whenever the window is resized
    window.addEventListener('resize', () => {
        resizeCanvas(); // Recalculate canvas size and font sizes
        // On resize, you might want to clear the canvas and immediately redraw text
        // to avoid temporary distortions before the pixels fill in.
        // ctx.clearRect(0, 0, canvas.width, canvas.height); // Optional: clear on resize
    });
});
