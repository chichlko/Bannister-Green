### Environment Capture
This represents initial forays into 'real-time' environment capture, beginning with audio. First things first, to get going on this I stood on the shoulders of Mark Jay:<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;https://github.com/markjay4k/Audio-Spectrum-Analyzer-in-Python/blob/master/audio_spectrumQT.py<p>
He also provides some great youtube presentations at:
<ul><li>https://www.youtube.com/watch?v=AShHJdSIxkY</li>
    <li>https://www.youtube.com/watch?v=aQKX3mrDFoY</li>
    <li>https://www.youtube.com/watch?v=RHmTgapLu4s</li></ul><p>
While this runs okay on my laptop I ended up switching off any microphone noise/echo cancellation and I had to keep my voice low, otherwise I would run into rails quickly enough.  Also, the update rate, at just over five updates per second, is to low to properly capture all speech nuances; I’m hoping that decoupling from waveform and spectrum real-time plotting in later versions will raise this to suitable levels.<p>
You're prompted to provide a filename for the spectrogram (a .npydat extension is added if not already there).  I'm hoping to use these to help train a neural net, in particular, a self-constructing version which came out of my PhD work.

