define i32 @pattern_lshr_8_32(i32 %x) {
entry:
  %result = lshr i32 %x, 8
  ret i32 %result
}
