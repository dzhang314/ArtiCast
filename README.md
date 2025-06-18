# ArtiCast

**ArtiCast** is an open-source tool that turns academic papers into natural, well-spoken audio, allowing you to keep up with the latest research developments while driving, exercising, or doing chores.

### Features

 * **ArtiCast reads the actual paper.** Unlike summarization tools, like [NotebookLM](https://notebooklm.google/), which omit crucial details, **ArtiCast** reads the full text of the original paper.

 * **ArtiCast cuts through the noise.** It uses [**GROBID**](https://github.com/kermitt2/grobid) to isolate the main text of the paper from headers, footnotes, page numbers, and citations, which confuse other text-to-speech applications.

 * **ArtiCast maintains flow.** Unlike competing tools, like [Paper2Audio](https://www.paper2audio.com/), which interrupt the flow of ideas with overly verbose descriptions, **ArtiCast** succinctly incorporates figures and formulas into its narration.

   Compare Paper2Audio's long, noisy description of [Equation 1 from this paper](https://pubs.aip.org/aip/jcp/article/120/17/7877/534771/A-growing-string-method-for-determining-transition):

   $$ \mathbf{f}^{\perp}(\varphi(\sigma)) = - \nabla V(\varphi(\sigma)) + (\hat{\mathbf{t}}(\sigma)^T \nabla V(\varphi(\sigma))) \hat{\mathbf{t}}(\sigma) $$

   > ... then the normal force on the string at sigma can be defined as:
   > 
   > MATH SUMMARY: This expression calculates the normal force acting on a string during an evolution step. It starts by computing the negative gradient of a potential function at a specific point on the string. Then, it calculates the projection of this gradient onto the unit tangent vector at that point. This projection is then multiplied by the unit tangent vector itself. Finally, it subtracts the negative gradient from the scaled tangent vector projection. The result is the normal force, which represents the force acting perpendicular to the string at that point, guiding the string towards a minimum energy pathway.

   to **ArtiCast**'s concise narration, highlighting the underlying geometric idea:

   > then the normal force on the string at sigma can be defined as the component of the negative potential gradient that is perpendicular to the string's unit tangent vector at that point.

### Setup

**ArtiCast** requires a Python environment with [google-genai](https://github.com/googleapis/python-genai) and [grobid-client-python](https://github.com/kermitt2/grobid_client_python). A Gemini API key must be provided as the environment variable `GEMINI_API_KEY`, and a GROBID instance is expected to be running on the default port (`localhost:8070`).

### Limitations

**ArtiCast** uses machine learning technologies, such as optical character recognition (OCR) and large language models (LLMs), to extract and narrate text from papers. In some cases, **ArtiCast** performs minor edits to make the text more suitable for audio narration, such as spelling out abbreviations and replacing references to figures and equations. Although we take precautions to ensure that these edits do not change the intended meaning of the text, machine learning systems are inherently noisy and we cannot guarantee accuracy in all cases.

**ArtiCast** deliberately omits figure captions and bibliographic references in order to improve the flow of its narration, and it is inherently impossible to completely represent graphical figures using audio. If a paper contains substantive information found only in its figures or bibliographic references, this information may be omitted from narration.
