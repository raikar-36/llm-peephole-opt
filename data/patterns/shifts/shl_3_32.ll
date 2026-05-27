define i32 @pattern_shl_3_32(i32 %x) {
entry:
  %result = shl i32 %x, 3
  ret i32 %result
}
