define i32 @pattern_lshr_1_32(i32 %x) {
entry:
  %result = lshr i32 %x, 1
  ret i32 %result
}
