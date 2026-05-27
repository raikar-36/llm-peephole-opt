define i32 @pattern_ashr_2_32(i32 %x) {
entry:
  %result = ashr i32 %x, 2
  ret i32 %result
}
