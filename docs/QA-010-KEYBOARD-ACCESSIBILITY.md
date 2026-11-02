# QA-010 — keyboard accessibility (TalkBack still pending)

After QA-009 restores stock HOME on the disposable Android 15 emulator, QA-010 opens Mr. Nothing explicitly without changing the HOME role. It checks nonempty, unique accessible descriptions and focusable controls, then captures 16 UI hierarchy snapshots while sending ordinary TAB events. The gate requires focus on two different launcher buttons, including the stock-launcher recovery control. It captures focus labels and a screenshot. Ambiguity fails closed.

**Limitations:** This does not enable TalkBack, prove spoken labels, bypass accessibility-service consent, validate physical Pixel hardware, or certify WCAG. Real TalkBack navigation, touch exploration, switch access, contrast and independent review remain open. Runtime acceptance requires a successful GitHub Actions run.
