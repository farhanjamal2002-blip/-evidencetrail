# Third-party notices

## Gender Decoder word lists

EvidenceTrail adapts and conservatively curates the masculine-coded and
feminine-coded English word-prefix lists from
[lovedaybrooke/gender-decoder](https://github.com/lovedaybrooke/gender-decoder),
released as `genderdecoder` 0.3. The ambiguous `lead` prefix is omitted because
it commonly appears in neutral job titles. The remaining lists are used only to
surface exact wording for human review. EvidenceTrail does not use the upstream
package's overall classification or explanation.

The upstream repository is licensed under the MIT License:

> Copyright (c) 2016 lovedaybrooke
>
> Permission is hereby granted, free of charge, to any person obtaining a copy
> of this software and associated documentation files (the "Software"), to deal
> in the Software without restriction, including without limitation the rights
> to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
> copies of the Software, and to permit persons to whom the Software is
> furnished to do so, subject to the following conditions:
>
> The above copyright notice and this permission notice shall be included in all
> copies or substantial portions of the Software.
>
> THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
> IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
> FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
> AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
> LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
> OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
> SOFTWARE.

The upstream project describes the lexicon's limits, including its binary
gender framing, in its README. Later research found gendered-wording effects can
depend on context. EvidenceTrail therefore keeps the list collapsed and
optional, labels matches as historical language-review cues, and never presents
them as a bias score, discrimination finding, or legal conclusion. See
[RESEARCH_NOTES.md](RESEARCH_NOTES.md) for the research summary.
