define i32 @pattern_lshr_3_32(i32 %x) {
entry:
  %result = lshr i32 %x, 3
  ret i32 %result
}
