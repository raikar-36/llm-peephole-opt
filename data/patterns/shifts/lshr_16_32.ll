define i32 @pattern_lshr_16_32(i32 %x) {
entry:
  %result = lshr i32 %x, 16
  ret i32 %result
}
