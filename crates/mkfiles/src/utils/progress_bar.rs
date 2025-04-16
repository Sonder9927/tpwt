use indicatif::{ProgressBar, ProgressStyle};

pub fn pbar(len: u64, msg: &str) -> ProgressBar {
        ProgressBar::new(len).with_style(
            ProgressStyle::with_template(&format!(
                "{{spinner:.green}} {}: [{{elapsed_precise}}] [{{wide_bar:.cyan/blue}}] {{pos}}/{{len}} ({{eta}})",
                msg
            ))
            .unwrap()
            .progress_chars("#>-")
        )
    }